"""
HeliosPipeline REST API Server.

FastAPI backend serving magnetogram images, SolarNet predictions,
system statistics, and pipeline logs.
"""

import io
import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
)
logger = logging.getLogger("helios.api")


# ---------------------------------------------------------------------------
# Paths (resolved relative to the HeliosPipeline root)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # HeliosPipeline/
DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "helios_v2_pro.pth"
LOG_DIR = BASE_DIR


# ---------------------------------------------------------------------------
# SolarNet Architecture (mirrored from src/models/train_model.py)
# ---------------------------------------------------------------------------

class SolarNet(nn.Module):
    """
    CNN for solar activity prediction.

    Architecture: 4 convolutional blocks with BatchNorm, Dropout,
    Global Average Pooling, and a single regression output.

    Input:  (batch, 1, 512, 512) -- normalized magnetograms
    Output: (batch, 1) -- predicted sunspot index
    """

    def __init__(self, dropout_rate: float = 0.3) -> None:
        super().__init__()

        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout1 = nn.Dropout2d(p=dropout_rate)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout2 = nn.Dropout2d(p=dropout_rate)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout3 = nn.Dropout2d(p=dropout_rate)

        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout4 = nn.Dropout2d(p=dropout_rate)

        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, 1)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for conv, bn, pool, drop in [
            (self.conv1, self.bn1, self.pool1, self.dropout1),
            (self.conv2, self.bn2, self.pool2, self.dropout2),
            (self.conv3, self.bn3, self.pool3, self.dropout3),
            (self.conv4, self.bn4, self.pool4, self.dropout4),
        ]:
            x = drop(pool(self.relu(bn(conv(x)))))
        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


# ---------------------------------------------------------------------------
# Grad-CAM (Explainable AI)
# ---------------------------------------------------------------------------

class GradCAM:
    """
    Gradient-weighted Class Activation Mapping for SolarNet.

    Visualizes which regions of the input magnetogram the model focuses on.
    Uses the last convolutional layer (conv4) to generate heatmaps.
    """

    def __init__(self, model: SolarNet, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self.hooks: List = []

    def _save_gradient(self, grad: torch.Tensor) -> None:
        self.gradients = grad

    def _save_activation(self, module: nn.Module, input: tuple, output: torch.Tensor) -> None:
        self.activations = output

    def register_hooks(self) -> None:
        """Register forward and backward hooks on the target layer."""
        def forward_hook(module, input, output):
            self._save_activation(module, input, output)

        def backward_hook(module, grad_input, grad_output):
            self._save_gradient(grad_output[0])

        self.hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self.hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def remove_hooks(self) -> None:
        """Clean up all registered hooks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []

    def generate_heatmap(self, input_tensor: torch.Tensor) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for the input tensor.

        Args:
            input_tensor: (1, 1, H, W) normalized magnetogram

        Returns:
            (H, W) heatmap array normalized to [0, 1]
        """
        self.model.eval()
        self.register_hooks()

        try:
            # Forward pass
            output = self.model(input_tensor)
            self.model.zero_grad()

            # Backward pass (target = output for regression)
            output.backward()

            # Compute weights: global average pooling of gradients
            pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])

            # Weight the activations by the gradients
            for i in range(self.activations.shape[1]):
                self.activations[:, i, :, :] *= pooled_gradients[i]

            # Average across channels and ReLU
            heatmap = torch.mean(self.activations, dim=1).squeeze()
            heatmap = torch.maximum(heatmap, torch.tensor(0.0))

            # Normalize to [0, 1]
            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()

            return heatmap.detach().cpu().numpy()

        finally:
            self.remove_hooks()


# ---------------------------------------------------------------------------
# Device Detection
# ---------------------------------------------------------------------------

def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

_model: Optional[SolarNet] = None
_device: Optional[torch.device] = None


def _load_model() -> None:
    """Load SolarNet weights into global state (called once at startup)."""
    global _model, _device

    _device = _get_device()
    logger.info("Device selected: %s", _device)

    if not MODEL_PATH.exists():
        logger.error("Model file not found: %s", MODEL_PATH)
        return

    _model = SolarNet(dropout_rate=0.3)
    _model.load_state_dict(torch.load(MODEL_PATH, map_location=_device))
    _model.eval()
    _model.to(_device)

    total_params = sum(p.numel() for p in _model.parameters())
    logger.info("SolarNet loaded: %s parameters, weights: %s", f"{total_params:,}", MODEL_PATH.name)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ImageListItem(BaseModel):
    filename: str
    date: Optional[str] = None
    size_bytes: int


class ImageListResponse(BaseModel):
    images: List[ImageListItem]
    total: int


class PredictionResult(BaseModel):
    sunspot_index: float
    risk_level: str
    confidence: float


class SystemStats(BaseModel):
    total_images: int
    disk_usage_mb: float
    mae: float
    last_updated: str


class LogEntry(BaseModel):
    filename: str
    lines: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_PATTERN = re.compile(
    r"hmi\.m_45s\.(\d{4})\.(\d{2})\.(\d{2})_(\d{2})_(\d{2})_(\d{2})_TAI"
)


def _extract_date(filename: str) -> Optional[str]:
    """Extract ISO-8601 date string from an HMI filename."""
    match = _DATE_PATTERN.search(filename)
    if not match:
        return None
    y, mo, d, h, mi, s = match.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:{s}Z"


def _classify_risk(sunspot_index: float) -> str:
    """Map sunspot index to a risk category."""
    if sunspot_index < 30.0:
        return "Low"
    if sunspot_index < 70.0:
        return "Medium"
    return "High"


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    _load_model()
    yield
    logger.info("Shutting down HeliosPipeline API")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HeliosPipeline API",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="2.1.0")


# -- Images ----------------------------------------------------------------

@app.get("/api/images/list", response_model=ImageListResponse)
async def list_images():
    """Return all .npy files in data/processed/, sorted by date descending."""
    if not DATA_DIR.exists():
        raise HTTPException(status_code=500, detail=f"Data directory not found: {DATA_DIR}")

    items: List[ImageListItem] = []
    for path in sorted(DATA_DIR.glob("*.npy")):
        items.append(
            ImageListItem(
                filename=path.name,
                date=_extract_date(path.name),
                size_bytes=path.stat().st_size,
            )
        )

    # Sort by date descending (most recent first); entries without date go last
    items.sort(key=lambda i: i.date or "", reverse=True)

    return ImageListResponse(images=items, total=len(items))


@app.get("/api/images/{filename}")
async def get_image(filename: str):
    """
    Render a .npy magnetogram as a PNG using the RdBu_r colormap.

    The data is expected to be normalized in [-1, 1].
    Returns a streaming PNG response suitable for <img src="...">.
    """
    filepath = DATA_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".npy":
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    data: np.ndarray = np.load(str(filepath))

    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
    ax.imshow(data, cmap="RdBu_r", vmin=-1, vmax=1, origin="lower")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, dpi=120)
    plt.close(fig)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


# -- Prediction ------------------------------------------------------------

@app.get("/api/predict/{filename}", response_model=PredictionResult)
async def predict(filename: str):
    """Run SolarNet inference on a processed .npy magnetogram."""
    if _model is None or _device is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    filepath = DATA_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".npy":
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    # Load and prepare tensor: (H, W) -> (1, 1, H, W)
    data: np.ndarray = np.load(str(filepath))
    tensor = torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0)
    tensor = tensor.to(_device)

    with torch.no_grad():
        prediction = _model(tensor)

    sunspot_index = round(float(prediction.item()), 4)
    risk_level = _classify_risk(sunspot_index)

    # Confidence heuristic: inversely related to absolute magnitude
    # High values have slightly lower confidence due to rarity in training data
    confidence = round(max(0.75, min(0.99, 1.0 - abs(sunspot_index) / 500.0)), 2)

    logger.info(
        "Prediction for %s: sunspot_index=%.4f, risk=%s, confidence=%.2f",
        filename, sunspot_index, risk_level, confidence,
    )

    return PredictionResult(
        sunspot_index=sunspot_index,
        risk_level=risk_level,
        confidence=confidence,
    )


# -- Explainability (Grad-CAM) ----------------------------------------------

@app.get("/api/explain/{filename}")
async def explain(filename: str):
    """
    Generate Grad-CAM visualization for a magnetogram.

    Returns a PNG with the heatmap overlaid on the original image,
    showing which regions the model focuses on during prediction.
    """
    if _model is None or _device is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    filepath = DATA_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".npy":
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    # Load and prepare tensor
    data: np.ndarray = np.load(str(filepath))
    tensor = torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0)
    tensor = tensor.to(_device)
    tensor.requires_grad = True

    # Generate Grad-CAM heatmap
    gradcam = GradCAM(_model, _model.conv4)
    heatmap = gradcam.generate_heatmap(tensor)

    # Resize heatmap to match original image size (32x32 -> 512x512)
    from scipy.ndimage import zoom
    zoom_factor = data.shape[0] / heatmap.shape[0]
    heatmap_resized = zoom(heatmap, zoom_factor, order=1)

    # Create the visualization
    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)

    # Base image: magnetogram with RdBu_r
    ax.imshow(data, cmap="RdBu_r", vmin=-1, vmax=1, origin="lower")

    # Overlay heatmap with transparency
    ax.imshow(
        heatmap_resized,
        cmap="inferno",
        alpha=0.4,
        origin="lower",
        vmin=0,
        vmax=1,
    )

    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, dpi=120)
    plt.close(fig)
    buf.seek(0)

    logger.info("Grad-CAM heatmap generated for %s", filename)

    return StreamingResponse(buf, media_type="image/png")


# -- Stats -----------------------------------------------------------------

@app.get("/api/stats", response_model=SystemStats)
async def get_stats():
    """Return dataset statistics: image count, disk usage, and MAE."""
    if not DATA_DIR.exists():
        raise HTTPException(status_code=500, detail="Data directory not found")

    npy_files = list(DATA_DIR.glob("*.npy"))
    total_images = len(npy_files)
    disk_bytes = sum(f.stat().st_size for f in npy_files)
    disk_mb = round(disk_bytes / (1024 * 1024), 2)

    # MAE from last training run (training_v2_pro.log)
    mae_value = 0.1416

    # Determine last modification time of any .npy
    if npy_files:
        latest = max(f.stat().st_mtime for f in npy_files)
        from datetime import datetime, timezone
        last_updated = datetime.fromtimestamp(latest, tz=timezone.utc).isoformat()
    else:
        last_updated = "N/A"

    return SystemStats(
        total_images=total_images,
        disk_usage_mb=disk_mb,
        mae=mae_value,
        last_updated=last_updated,
    )


# -- Logs ------------------------------------------------------------------

@app.get("/api/logs", response_model=List[LogEntry])
async def get_logs():
    """Read the last 50 lines from each .log file in the project root."""
    log_files = sorted(LOG_DIR.glob("*.log"))

    if not log_files:
        return []

    entries: List[LogEntry] = []
    for lf in log_files:
        try:
            with open(lf, "r", encoding="utf-8", errors="replace") as fh:
                all_lines = fh.readlines()
                tail = [line.rstrip("\n") for line in all_lines[-50:]]
            entries.append(LogEntry(filename=lf.name, lines=tail))
        except OSError as exc:
            logger.error("Failed to read log file %s: %s", lf.name, exc)

    return entries
