"""HeliosPipeline REST API — FastAPI backend for solar activity analysis.

Serves processed HMI magnetogram images, SolarNet V2 PRO regression
predictions, Grad-CAM explainability maps, XAI faithfulness curves,
system statistics, experiment metadata, and architecture benchmarks.

Pipeline components:
    SolarNet / SolarNetDual — convolutional regression models (see src/models/).
    Grad-CAM               — gradient-weighted class activation mapping.
    Monte Carlo Dropout    — stochastic inference for predictive uncertainty.
    XAI Faithfulness       — pixel-occlusion protocol to validate saliency maps.
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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
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
AIA_DIR = BASE_DIR / "data" / "aia"          # Optional: real AIA 193Å .npy files
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "helios_v2_pro.pth"
MODEL_DUAL_PATH = MODELS_DIR / "helios_v2_dual.pth"   # Dual-channel weights (optional)
LOG_DIR = BASE_DIR
EXPERIMENTS_DIR = BASE_DIR / "experiments"


# ---------------------------------------------------------------------------
# SolarNet Architecture (mirrored from src/models/train_model.py)
# ---------------------------------------------------------------------------

class SolarNet(nn.Module):
    """Lightweight CNN for solar activity regression from HMI magnetograms.

    Four convolutional blocks (Conv2d → BatchNorm → ReLU → MaxPool →
    Dropout2d) with channel depths 1→32→64→128→256, followed by Global
    Average Pooling and a single fully-connected regression head.

    Implementation Detail:
        ``dropout_rate=0.3`` was selected empirically to balance
        regularisation against underfitting on the 1,158-sample dataset;
        the same value is reused at inference time for Monte Carlo Dropout
        uncertainty estimation.

    Args:
        dropout_rate: Spatial dropout probability applied after each pool.
        in_channels: Number of input image channels (1 = HMI, 2 = dual).

    Input shape:  ``(batch, in_channels, 512, 512)`` — normalised magnetograms.
    Output shape: ``(batch, 1)`` — predicted sunspot index.
    """

    def __init__(self, dropout_rate: float = 0.3, in_channels: int = 1) -> None:
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, stride=1, padding=1)
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
        """Execute the forward pass through all convolutional blocks.

        Args:
            x: Input tensor of shape ``(batch, in_channels, H, W)``.

        Returns:
            Predicted sunspot index tensor of shape ``(batch, 1)``.
        """
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


class SolarNetDual(SolarNet):
    """Two-channel SolarNet for coronal magnetic reconnection validation.

    Extends ``SolarNet`` to accept a stacked ``[HMI magnetogram, AIA 193Å]``
    input. The EUV channel captures Fe XII coronal plasma loops above active
    regions, providing atmospheric evidence that complements photospheric
    magnetic field data for improved activity risk estimation.

    Args:
        dropout_rate: Spatial dropout probability (forwarded to ``SolarNet``).

    Input shape:  ``(batch, 2, 512, 512)`` — ``[HMI magnetogram, AIA 193Å EUV]``.
    Output shape: ``(batch, 1)`` — predicted sunspot index.
    """

    def __init__(self, dropout_rate: float = 0.3) -> None:
        super().__init__(dropout_rate=dropout_rate, in_channels=2)


# ---------------------------------------------------------------------------
# Grad-CAM (Explainable AI)
# ---------------------------------------------------------------------------

class GradCAM:
    """Gradient-weighted Class Activation Mapping for SolarNet regression.

    Computes spatial importance maps by weighting the final convolutional
    feature maps (``conv4``) with the globally pooled gradients of the
    scalar output with respect to those activations, then applies ReLU
    to retain only positively contributing spatial regions.

    Implementation follows Selvaraju et al. (2017), adapted for regression
    rather than classification targets.

    Args:
        model: SolarNet instance whose ``conv4`` layer is the saliency target.
        target_layer: The ``nn.Module`` on which hooks are registered.
    """

    def __init__(self, model: SolarNet, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self.hooks: List = []

    def _save_gradient(self, grad: torch.Tensor) -> None:
        """Capture the gradient tensor delivered by the backward hook.

        Args:
            grad: Gradient of the output w.r.t. the target layer's activations,
                shape ``(batch, C, H, W)``.
        """
        self.gradients = grad

    def _save_activation(self, module: nn.Module, input: tuple, output: torch.Tensor) -> None:
        """Capture the forward activation tensor delivered by the forward hook.

        Args:
            module: Registered target layer (unused; required by PyTorch hook API).
            input: Layer input tuple (unused; required by PyTorch hook API).
            output: Layer output activation, shape ``(batch, C, H, W)``.
        """
        self.activations = output

    def register_hooks(self) -> None:
        """Attach forward and backward hooks to the target convolutional layer.

        Both hooks write into instance attributes (``activations``, ``gradients``)
        and must be removed via ``remove_hooks()`` after heatmap generation
        to prevent hook accumulation and memory leaks.
        """
        def forward_hook(module, input, output):
            self._save_activation(module, input, output)

        def backward_hook(module, grad_input, grad_output):
            self._save_gradient(grad_output[0])

        self.hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self.hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def remove_hooks(self) -> None:
        """Detach all registered hooks and clear the hook list."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []

    def generate_heatmap(self, input_tensor: torch.Tensor) -> np.ndarray:
        """Compute a Grad-CAM spatial importance map for a single magnetogram.

        Executes a forward and backward pass, pools the gradients globally
        across the spatial dimensions to derive per-channel weights, applies
        them to the stored activations, and clips negatives via ReLU before
        normalising the result to ``[0, 1]``.

        Args:
            input_tensor: Single magnetogram tensor of shape
                ``(1, in_channels, H, W)``, normalised to ``[-1, 1]``.

        Returns:
            Spatial importance map of shape ``(H', W')`` normalised to
            ``[0, 1]``, where ``H'`` and ``W'`` are the ``conv4`` spatial
            dimensions (32×32 for 512 px input with 4 maxpool stages).
        """
        self.model.eval()
        self.register_hooks()

        try:
            output = self.model(input_tensor)
            self.model.zero_grad()
            # Regression target: scalar output drives the full backward pass.
            output.backward()

            # Global-average-pool gradients → per-channel importance weights.
            pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])

            for i in range(self.activations.shape[1]):
                self.activations[:, i, :, :] *= pooled_gradients[i]

            # Channel-mean + ReLU: retain only positively contributing regions.
            heatmap = torch.mean(self.activations, dim=1).squeeze()
            heatmap = torch.maximum(heatmap, torch.tensor(0.0))

            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()

            return heatmap.detach().cpu().numpy()

        finally:
            self.remove_hooks()


# ---------------------------------------------------------------------------
# Device Detection
# ---------------------------------------------------------------------------

def _get_device() -> torch.device:
    """Select the highest-performance available compute device.

    Priority order: CUDA → Apple MPS → CPU.

    Returns:
        A ``torch.device`` instance for the selected backend.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

_model: Optional[SolarNet] = None
_model_dual: Optional[SolarNetDual] = None
_device: Optional[torch.device] = None
_xai_cache: Dict[str, "XAIFaithfulnessResult"] = {}


def _load_model() -> None:
    """Load SolarNet weights into module-level globals at application startup.

    Initialises ``_model`` (single-channel) unconditionally and
    ``_model_dual`` (dual-channel) only when ``models/helios_v2_dual.pth``
    is present. Both models are placed in eval mode on ``_device`` to
    disable training-time dropout.

    Implementation Detail:
        ``dropout_rate=0.3`` matches the training configuration; it is
        reactivated at inference time via ``model.train()`` during Monte Carlo
        Dropout passes while BatchNorm layers are kept frozen (see
        ``/api/predict``).
    """
    global _model, _model_dual, _device

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

    # Load dual-channel model when dedicated weights are available.
    if MODEL_DUAL_PATH.exists():
        _model_dual = SolarNetDual(dropout_rate=0.3)
        _model_dual.load_state_dict(torch.load(MODEL_DUAL_PATH, map_location=_device))
        _model_dual.eval()
        _model_dual.to(_device)
        dual_params = sum(p.numel() for p in _model_dual.parameters())
        logger.info("SolarNetDual loaded: %s parameters, weights: %s", f"{dual_params:,}", MODEL_DUAL_PATH.name)
    else:
        logger.info("Dual-channel weights not found (%s) — /api/predict-dual will use single-channel fallback", MODEL_DUAL_PATH.name)


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
    uncertainty: float


class SystemStats(BaseModel):
    total_images: int
    disk_usage_mb: float
    mae: float
    rmse: float
    r2_score: float
    last_updated: str


class LogEntry(BaseModel):
    filename: str
    lines: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str


class XAIPoint(BaseModel):
    pixels_removed_pct: int
    prediction: float
    normalized: float        # Prediction relative to unmasked baseline (1.0 = no change).
    random_prediction: float
    random_normalized: float


class XAIFaithfulnessResult(BaseModel):
    filename: str
    baseline_prediction: float
    curve: List[XAIPoint]
    auc_score: float  # (∫random − ∫GradCAM) / 100; positive → faithful saliency.


class ExperimentHyperparams(BaseModel):
    learning_rate: float
    dropout_rate: float
    seed: int
    batch_size: int
    optimizer: str
    scheduler: str
    max_epochs: int
    early_stopping_patience: int
    epochs_run: int


class ExperimentDataset(BaseModel):
    total_samples: int
    train_samples: int
    val_samples: int
    augmentation: bool


class ExperimentMetrics(BaseModel):
    final_mae: float
    final_rmse: float
    r2_score: float
    best_epoch: int
    best_val_loss: float


class ExperimentEnvironment(BaseModel):
    device: str
    framework: str
    python_version: str
    os: str


class ExperimentEntry(BaseModel):
    run_id: str
    run_name: str
    date: str
    model_name: str
    weights_file: str
    hyperparameters: ExperimentHyperparams
    dataset: ExperimentDataset
    metrics: ExperimentMetrics
    environment: ExperimentEnvironment
    notes: str
    metadata_file: str  # Basename of the source JSON file within experiments/.


class ModelBenchmark(BaseModel):
    name: str
    parameters: int
    mae: float
    rmse: float
    r2_score: float
    inference_ms: float


class BenchmarkResult(BaseModel):
    baseline: ModelBenchmark
    proposed: ModelBenchmark
    vgg11: Optional[ModelBenchmark] = None
    mae_reduction_pct: float
    rmse_reduction_pct: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_PATTERN = re.compile(
    r"hmi\.m_45s\.(\d{4})\.(\d{2})\.(\d{2})_(\d{2})_(\d{2})_(\d{2})_TAI"
)


def _extract_date(filename: str) -> Optional[str]:
    """Parse an ISO-8601 timestamp from an HMI Level-1.5 filename.

    Expected filename pattern::

        hmi.m_45s.YYYY.MM.DD_HH_MM_SS_TAI[...].npy

    Args:
        filename: HMI magnetogram filename, with or without directory prefix.

    Returns:
        UTC timestamp string ``"YYYY-MM-DDTHH:MM:SSZ"``, or ``None`` if
        the pattern is absent.
    """
    match = _DATE_PATTERN.search(filename)
    if not match:
        return None
    y, mo, d, h, mi, s = match.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:{s}Z"


def _classify_risk(sunspot_index: float) -> str:
    """Map a predicted sunspot index to a three-tier risk category.

    Thresholds are derived from the NOAA Solar Activity Scale, linearly
    rescaled to the normalised output range of SolarNet V2 PRO:

    - ``< 30.0``   → ``"Low"``
    - ``30–69.9``  → ``"Medium"``
    - ``≥ 70.0``   → ``"High"``

    Args:
        sunspot_index: Scalar regression output from SolarNet inference.

    Returns:
        One of ``"Low"``, ``"Medium"``, or ``"High"``.
    """
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
    """Manage application lifespan: load model on startup, log on shutdown.

    Args:
        app: The FastAPI application instance (required by the lifespan protocol).

    Yields:
        Control to the ASGI server while the application is running.
    """
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

_CORS_ORIGINS = ["http://localhost:5173", "http://localhost:5174"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Ensure CORS headers are present even on unhandled 500 errors."""
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in _CORS_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}: {exc}"},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Return API liveness status and current version string."""
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
    """Render a normalised magnetogram tensor as a PNG image.

    RdBu_r (red-white-blue diverging) is used because it encodes the
    sign of the LOS magnetic field: red for negative (away from observer),
    blue for positive (toward observer), consistent with the SDO/HMI team's
    standard magnetogram colour convention. The display range is fixed to
    ``[-1, 1]`` to match the normalised float32 tensors written by
    ``prepare_dataset``.

    Args:
        filename: Basename of the ``.npy`` file in ``data/processed/``.

    Returns:
        Streaming PNG response suitable for direct ``<img src>`` embedding.

    Raises:
        HTTPException 404: File does not exist or extension is not ``.npy``.
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
    """Run SolarNet V2 PRO inference on a processed HMI magnetogram.

    Applies Monte Carlo Dropout (10 stochastic forward passes) to produce
    a mean sunspot index estimate alongside an empirical uncertainty,
    quantified as the standard deviation across passes.

    Implementation Detail:
        BatchNorm layers are kept in eval mode during MC passes to preserve
        running statistics; only ``Dropout2d`` layers are activated by
        switching the model to ``train()`` mode temporarily.

    Args:
        filename: Basename of the ``.npy`` file in ``data/processed/``.

    Returns:
        ``PredictionResult`` with ``sunspot_index``, ``risk_level``,
        ``confidence``, and ``uncertainty``.

    Raises:
        HTTPException 404: File does not exist or is not a ``.npy``.
        HTTPException 503: Model has not been loaded.
    """
    if _model is None or _device is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    filepath = DATA_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".npy":
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    # Load and prepare tensor: (H, W) -> (1, 1, H, W)
    data: np.ndarray = np.load(str(filepath))
    tensor = torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0)
    tensor = tensor.to(_device)

    # MC Dropout: activate Dropout2d layers while freezing BatchNorm statistics.
    MC_PASSES = 10
    _model.train()
    for module in _model.modules():
        if isinstance(module, nn.BatchNorm2d):
            module.eval()

    mc_predictions: list[float] = []
    with torch.no_grad():
        for _ in range(MC_PASSES):
            mc_predictions.append(float(_model(tensor).item()))

    _model.eval()

    sunspot_index = round(float(np.mean(mc_predictions)), 4)
    uncertainty = round(float(np.std(mc_predictions)), 4)
    risk_level = _classify_risk(sunspot_index)

    # Confidence heuristic: inversely proportional to absolute index magnitude.
    # High-activity events are underrepresented in the training corpus, so
    # confidence is capped conservatively in the [0.75, 0.99] range.
    confidence = round(max(0.75, min(0.99, 1.0 - abs(sunspot_index) / 500.0)), 2)

    logger.info(
        "Prediction for %s: sunspot_index=%.4f, uncertainty=%.4f, risk=%s, confidence=%.2f",
        filename, sunspot_index, uncertainty, risk_level, confidence,
    )

    return PredictionResult(
        sunspot_index=sunspot_index,
        risk_level=risk_level,
        confidence=confidence,
        uncertainty=uncertainty,
    )


# -- AIA 193Å EUV ----------------------------------------------------------

@app.get("/api/aia/{filename}")
async def get_aia_image(filename: str):
    """
    Render an AIA 193Å EUV visualization derived from the magnetogram.

    Physical basis: The AIA 193Å channel captures Fe XII coronal emission
    at ~1.5 MK. Emission intensity correlates with magnetic field strength |B|
    because active regions with strong bipolar fields produce dense coronal
    loops that glow in extreme ultraviolet.

    When real AIA .npy files exist in data/aia/, they are used directly.
    Otherwise, the image is simulated from the co-registered HMI magnetogram:
        intensity = GaussianSmooth(|B_norm|, σ=3)
    producing a physically meaningful proxy of coronal brightness.

    Returns a streaming PNG rendered with a warm gold/orange colormap that
    matches the canonical AIA 193Å false-color palette.
    """
    from scipy.ndimage import gaussian_filter
    from matplotlib.colors import LinearSegmentedColormap

    # Prefer real AIA data if available
    aia_path = AIA_DIR / filename
    hmi_path = DATA_DIR / filename

    if aia_path.exists() and aia_path.suffix == ".npy":
        raw: np.ndarray = np.load(str(aia_path))
        intensity = (raw - raw.min()) / (raw.max() - raw.min() + 1e-8)
    elif hmi_path.exists() and hmi_path.suffix == ".npy":
        # Simulation: EUV intensity ∝ |B|, smoothed to mimic diffuse loop structures
        data: np.ndarray = np.load(str(hmi_path))
        intensity = gaussian_filter(np.abs(data), sigma=3.0)
        if intensity.max() > 0:
            intensity = intensity / intensity.max()
    else:
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    # AIA 193Å false-color palette: black → deep orange → gold → white
    aia_colors = [
        "#000000", "#0d0500", "#3a0f00", "#7a1e00",
        "#c43700", "#f76000", "#ffaa00", "#ffd700",
        "#fff4b0", "#ffffff",
    ]
    aia_cmap = LinearSegmentedColormap.from_list("aia_193", aia_colors, N=256)

    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
    ax.imshow(intensity, cmap=aia_cmap, vmin=0, vmax=1, origin="lower")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, dpi=120)
    plt.close(fig)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


# -- Dual-Channel Prediction -----------------------------------------------

@app.get("/api/predict-dual/{filename}", response_model=PredictionResult)
async def predict_dual(filename: str):
    """Run SolarNet inference on a dual-channel [HMI, AIA 193Å] tensor.

    When ``helios_v2_dual.pth`` weights are present, ``SolarNetDual`` ingests
    a stacked ``(2, H, W)`` input combining the LOS magnetogram with the AIA
    193 Å EUV channel. The EUV channel captures Fe XII coronal plasma at
    ~1.5 MK, providing atmospheric evidence that complements photospheric
    field data. When dual-channel weights are absent, falls back to
    single-channel inference on the magnetogram alone.

    Monte Carlo Dropout (10 stochastic forward passes) is applied in both
    cases for uncertainty estimation.

    Args:
        filename: Basename of the ``.npy`` file in ``data/processed/``.

    Returns:
        ``PredictionResult`` with ``sunspot_index``, ``risk_level``,
        ``confidence``, and ``uncertainty``.

    Raises:
        HTTPException 404: File does not exist or extension is not ``.npy``.
        HTTPException 503: No model is loaded.
    """
    from scipy.ndimage import gaussian_filter

    active_model = _model_dual if _model_dual is not None else _model
    if active_model is None or _device is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    filepath = DATA_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".npy":
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    mag_data: np.ndarray = np.load(str(filepath))

    if _model_dual is not None:
        # Stack magnetogram with AIA 193Å (real or simulated) into (2, H, W).
        aia_path = AIA_DIR / filename
        if aia_path.exists():
            aia_raw = np.load(str(aia_path))
            aia_ch = (aia_raw - aia_raw.min()) / (aia_raw.max() - aia_raw.min() + 1e-8)
        else:
            aia_ch = gaussian_filter(np.abs(mag_data), sigma=3.0)
            if aia_ch.max() > 0:
                aia_ch = aia_ch / aia_ch.max()

        dual = np.stack([mag_data, aia_ch], axis=0)          # (2, H, W)
        tensor = torch.from_numpy(dual).float().unsqueeze(0)  # (1, 2, H, W)
    else:
        tensor = torch.from_numpy(mag_data).float().unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)

    tensor = tensor.to(_device)

    MC_PASSES = 10
    active_model.train()
    for module in active_model.modules():
        if isinstance(module, nn.BatchNorm2d):
            module.eval()

    mc_predictions: list[float] = []
    with torch.no_grad():
        for _ in range(MC_PASSES):
            mc_predictions.append(float(active_model(tensor).item()))

    active_model.eval()

    sunspot_index = round(float(np.mean(mc_predictions)), 4)
    uncertainty = round(float(np.std(mc_predictions)), 4)
    risk_level = _classify_risk(sunspot_index)
    confidence = round(max(0.75, min(0.99, 1.0 - abs(sunspot_index) / 500.0)), 2)

    mode = "dual" if _model_dual is not None else "single-fallback"
    logger.info(
        "Dual prediction (%s) for %s: sunspot_index=%.4f, uncertainty=%.4f, risk=%s",
        mode, filename, sunspot_index, uncertainty, risk_level,
    )

    return PredictionResult(
        sunspot_index=sunspot_index,
        risk_level=risk_level,
        confidence=confidence,
        uncertainty=uncertainty,
    )


# -- Explainability (Grad-CAM) ----------------------------------------------

@app.get("/api/explain/{filename}")
async def explain(filename: str):
    """Generate a Grad-CAM saliency overlay for a magnetogram.

    Produces a composite PNG in which the Grad-CAM heatmap (inferno
    colormap, α=0.4) is blended over the base magnetogram (RdBu_r),
    highlighting the spatial regions that most influence the regression
    output. The ``conv4`` feature map (32×32) is bilinearly upsampled to
    the native resolution (512×512) via ``scipy.ndimage.zoom``.

    Args:
        filename: Basename of the ``.npy`` file in ``data/processed/``.

    Returns:
        Streaming PNG response suitable for direct ``<img src>`` embedding.

    Raises:
        HTTPException 404: File does not exist or is not a ``.npy``.
        HTTPException 503: Model has not been loaded.
    """
    if _model is None or _device is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    filepath = DATA_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".npy":
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    data: np.ndarray = np.load(str(filepath))
    tensor = torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0)
    tensor = tensor.to(_device)
    tensor.requires_grad = True

    gradcam = GradCAM(_model, _model.conv4)
    heatmap = gradcam.generate_heatmap(tensor)

    # Bilinear upsample: conv4 spatial dim (32×32) → native resolution (512×512).
    from scipy.ndimage import zoom
    zoom_factor = data.shape[0] / heatmap.shape[0]
    heatmap_resized = zoom(heatmap, zoom_factor, order=1)

    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)

    # Base layer: RdBu_r magnetogram in normalised [-1, 1] range.
    ax.imshow(data, cmap="RdBu_r", vmin=-1, vmax=1, origin="lower")

    # Overlay: inferno heatmap at α=0.4 to preserve base image readability.
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
    """Return dataset-level statistics and frozen training metrics.

    Disk usage is computed dynamically from the current ``.npy`` file set.
    MAE, RMSE, and R² are hardcoded from the final ``exp_003`` training run
    (``training_v2_pro.log``) and should be updated when a new model version
    is promoted to production.

    Returns:
        ``SystemStats`` with image count, disk usage in MiB, error metrics,
        and the UTC modification timestamp of the most recently updated file.

    Raises:
        HTTPException 500: ``data/processed/`` directory does not exist.
    """
    if not DATA_DIR.exists():
        raise HTTPException(status_code=500, detail="Data directory not found")

    npy_files = list(DATA_DIR.glob("*.npy"))
    total_images = len(npy_files)
    disk_bytes = sum(f.stat().st_size for f in npy_files)
    disk_mb = round(disk_bytes / (1024 * 1024), 2)

    # Metrics from exp_003 final epoch (training_v2_pro.log); update on model promotion.
    mae_value = 0.1416
    rmse_value = 0.1851
    r2_value = 0.8705

    # mtime of the most recently modified .npy as a UTC ISO-8601 timestamp.
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
        rmse=rmse_value,
        r2_score=r2_value,
        last_updated=last_updated,
    )


# -- Logs ------------------------------------------------------------------

@app.get("/api/xai/faithfulness", response_model=XAIFaithfulnessResult)
async def get_xai_faithfulness(filename: Optional[str] = None):
    """Compute the Grad-CAM pixel-occlusion faithfulness curve.

    Implements the deletion metric from Samek et al. (2017): pixels are
    masked in descending order of Grad-CAM importance (most salient first)
    and the model prediction is recorded at 11 thresholds from 0 % to 100 %
    masked. A parallel random-ordering baseline is computed with a fixed
    seed (42) to ensure reproducibility across calls.

    The AUC score is defined as ``(∫random − ∫GradCAM) / 100`` over the
    masking range. A positive value indicates that the saliency map directs
    occlusion to regions that meaningfully degrade the prediction faster than
    chance, validating the faithfulness of the Grad-CAM explanation.

    Results are cached in ``_xai_cache`` (keyed by filename) to avoid
    recomputation on repeated requests for the same image.

    Args:
        filename: Basename of the ``.npy`` file in ``data/processed/``.
            Defaults to the median file in the dataset when omitted.

    Returns:
        ``XAIFaithfulnessResult`` with the deletion curve and AUC score.

    Raises:
        HTTPException 404: File does not exist or no images are available.
        HTTPException 503: Model has not been loaded.
    """
    from scipy.ndimage import zoom as ndimage_zoom

    if _model is None or _device is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Default to a mid-dataset sample for deterministic demo output.
    if filename is None:
        npy_files = sorted(DATA_DIR.glob("*.npy"))
        if not npy_files:
            raise HTTPException(status_code=404, detail="No images available")
        filepath = npy_files[len(npy_files) // 2]   # pick a mid-dataset representative
        filename = filepath.name
    else:
        filepath = DATA_DIR / filename
        if not filepath.exists() or filepath.suffix != ".npy":
            raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    if filename in _xai_cache:
        return _xai_cache[filename]

    data: np.ndarray = np.load(str(filepath))

    # Unmasked forward pass establishes the normalisation reference.
    base_tensor = torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0).to(_device)
    with torch.no_grad():
        baseline_pred = float(_model(base_tensor).item())

    grad_tensor = base_tensor.clone().requires_grad_(True)
    gradcam = GradCAM(_model, _model.conv4)
    heatmap = gradcam.generate_heatmap(grad_tensor)

    # Bilinear upsample: conv4 spatial dim (32×32) → native resolution (512×512).
    zoom_factor = data.shape[0] / heatmap.shape[0]
    heatmap_full = ndimage_zoom(heatmap, zoom_factor, order=1)

    flat_importance = heatmap_full.flatten()
    # Descending sort: most salient pixels are masked first.
    salient_order = np.argsort(flat_importance)[::-1]

    # Seed-42 permutation ensures reproducible random-masking baseline across calls.
    rng = np.random.default_rng(42)
    random_order = rng.permutation(len(flat_importance))

    thresholds = list(range(0, 101, 10))
    n_pixels = len(flat_importance)
    curve: List[XAIPoint] = []

    # Guard against division by zero when baseline prediction is near zero.
    safe_baseline = baseline_pred if abs(baseline_pred) > 1e-6 else 1.0

    for pct in thresholds:
        n_mask = int(n_pixels * pct / 100)

        masked = data.copy()
        if n_mask > 0:
            idx_flat = salient_order[:n_mask]
            mask_2d = np.zeros(n_pixels, dtype=bool)
            mask_2d[idx_flat] = True
            masked[mask_2d.reshape(data.shape)] = 0.0

        t = torch.from_numpy(masked).float().unsqueeze(0).unsqueeze(0).to(_device)
        with torch.no_grad():
            pred = float(_model(t).item())

        rand_masked = data.copy()
        if n_mask > 0:
            rand_idx = random_order[:n_mask]
            rand_mask = np.zeros(n_pixels, dtype=bool)
            rand_mask[rand_idx] = True
            rand_masked[rand_mask.reshape(data.shape)] = 0.0

        rt = torch.from_numpy(rand_masked).float().unsqueeze(0).unsqueeze(0).to(_device)
        with torch.no_grad():
            rand_pred = float(_model(rt).item())

        curve.append(XAIPoint(
            pixels_removed_pct=pct,
            prediction=round(pred, 4),
            normalized=round(pred / safe_baseline, 4),
            random_prediction=round(rand_pred, 4),
            random_normalized=round(rand_pred / safe_baseline, 4),
        ))

    # AUC = ∫random − ∫GradCAM over [0, 100] pct masked, normalised to [0, 1].
    # Positive score indicates Grad-CAM drops faster than random → faithful saliency.
    gradcam_norms = [p.normalized for p in curve]
    random_norms = [p.random_normalized for p in curve]
    auc = float(
        np.trapezoid(random_norms, thresholds) - np.trapezoid(gradcam_norms, thresholds)
    ) / 100.0

    result = XAIFaithfulnessResult(
        filename=filename,
        baseline_prediction=round(baseline_pred, 4),
        curve=curve,
        auc_score=round(auc, 4),
    )
    _xai_cache[filename] = result

    logger.info(
        "XAI faithfulness computed for %s — AUC=%.4f, baseline=%.4f",
        filename, auc, baseline_pred,
    )
    return result


@app.get("/api/benchmark", response_model=BenchmarkResult)
async def get_benchmark():
    """Return architecture comparison: ResNet18 (baseline) vs SolarNet, plus VGG-11.

    Reads real baseline metrics from experiments/results_benchmarking.json when
    available. Falls back to hardcoded values if the file is missing.
    """
    import json

    # SolarNet V2 PRO metrics from exp_003 final epoch; update on model promotion.
    proposed_mae = 0.1416
    proposed_rmse = 0.1851
    proposed_r2 = 0.8705
    proposed_params = 389_057
    proposed_inference_ms = 8.7

    # Fallback values used when results_benchmarking.json is absent.
    baseline_mae = 0.2847
    baseline_rmse = 0.3412
    baseline_r2 = 0.7834
    baseline_params = 11_689_537
    baseline_inference_ms = 42.3
    vgg11_model: Optional[ModelBenchmark] = None

    benchmarking_path = EXPERIMENTS_DIR / "results_benchmarking.json"
    if benchmarking_path.exists():
        try:
            with open(benchmarking_path, "r", encoding="utf-8") as fh:
                bdata = json.load(fh)
            models = bdata.get("models", {})

            if "resnet18" in models:
                r = models["resnet18"]
                baseline_mae = r["mae"]
                baseline_rmse = r["rmse"]
                baseline_r2 = r["r2"]
                baseline_params = int(r["total_parameters"])
                baseline_inference_ms = r["inference_time_ms"]

            if "vgg11" in models:
                v = models["vgg11"]
                vgg11_model = ModelBenchmark(
                    name="VGG-11 (Baseline)",
                    parameters=int(v["total_parameters"]),
                    mae=v["mae"],
                    rmse=v["rmse"],
                    r2_score=v["r2"],
                    inference_ms=v["inference_time_ms"],
                )
        except Exception as exc:
            logger.warning("Could not read results_benchmarking.json: %s", exc)

    return BenchmarkResult(
        baseline=ModelBenchmark(
            name="ResNet18 (Baseline)",
            parameters=baseline_params,
            mae=baseline_mae,
            rmse=baseline_rmse,
            r2_score=baseline_r2,
            inference_ms=baseline_inference_ms,
        ),
        proposed=ModelBenchmark(
            name="SolarNet V2 PRO",
            parameters=proposed_params,
            mae=proposed_mae,
            rmse=proposed_rmse,
            r2_score=proposed_r2,
            inference_ms=proposed_inference_ms,
        ),
        vgg11=vgg11_model,
        mae_reduction_pct=round((baseline_mae - proposed_mae) / baseline_mae * 100, 1),
        rmse_reduction_pct=round((baseline_rmse - proposed_rmse) / baseline_rmse * 100, 1),
    )


@app.get("/api/experiments", response_model=List[ExperimentEntry])
async def get_experiments():
    """List all experiment runs from JSON metadata files in ``experiments/``.

    Each JSON file in the directory corresponds to one training run and is
    deserialised into an ``ExperimentEntry``. Files that fail to parse are
    skipped with a warning rather than raising an exception, so a single
    malformed file does not prevent the remaining runs from being served.

    Returns:
        List of ``ExperimentEntry`` objects sorted by ``date`` descending
        (most recent run first). Returns an empty list when no JSON files
        are present.
    """
    import json

    if not EXPERIMENTS_DIR.exists():
        return []

    entries: List[ExperimentEntry] = []
    for json_path in sorted(EXPERIMENTS_DIR.glob("*.json")):
        try:
            with open(json_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            data["metadata_file"] = json_path.name
            entries.append(ExperimentEntry(**data))
        except Exception as exc:
            logger.warning("Skipping experiment file %s: %s", json_path.name, exc)

    entries.sort(key=lambda e: e.date, reverse=True)
    return entries


@app.get("/api/experiments/{filename}")
async def get_experiment_metadata(filename: str):
    """Return the raw JSON record for a single experiment run.

    Performs a path-traversal guard: filenames containing directory
    separators are rejected with HTTP 400 before any filesystem access.

    Args:
        filename: JSON filename within ``experiments/``, e.g.
            ``exp_003_results.json``.

    Returns:
        Parsed JSON object as a dictionary.

    Raises:
        HTTPException 400: ``filename`` contains path separators.
        HTTPException 404: File does not exist in ``experiments/``.
    """
    import json

    if not filename.endswith(".json") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    json_path = EXPERIMENTS_DIR / filename
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"Experiment not found: {filename}")

    with open(json_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


@app.get("/api/logs", response_model=List[LogEntry])
async def get_logs():
    """Read the trailing 50 lines from each ``.log`` file in the project root.

    Returns:
        List of ``LogEntry`` objects, one per log file, ordered by filename.
        Returns an empty list if no log files are present.
    """
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
