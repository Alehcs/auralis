#!/usr/bin/env python3
"""Train and profile external CNN baselines for the Coronium comparison.

These models intentionally collapse B+/B- into one ``|B|`` channel because the
off-the-shelf ResNet/VGG definitions are used as broad reference points, not as
domain-specific competitors. Results feed the ``/api/benchmark`` endpoint.
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import models
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.train_model import SolarDataset  # noqa: E402

# ── Configuration ─────────────────────────────────────────────────────────────
SEED = 42
BATCH_SIZE = 32
NUM_EPOCHS = 30
LEARNING_RATE = 0.001
VAL_SPLIT = 0.2

DATA_DIR = PROJECT_ROOT / "data" / "processed"
METADATA_CSV = DATA_DIR / "metadata_processed.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "baselines"
RESULTS_PATH = PROJECT_ROOT / "experiments" / "results_benchmarking.json"

INFERENCE_WARMUP = 10
INFERENCE_RUNS = 100

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Utilities ─────────────────────────────────────────────────────────────────

def set_seed(seed: int) -> None:
    """Fix random state for reproducible splits and baseline initialisation."""
    torch.manual_seed(seed)
    np.random.seed(seed)


def get_device() -> torch.device:
    """Select Apple MPS, CUDA, or CPU in that order."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_dataloaders():
    """Create the deterministic 80/20 split used for baseline comparison."""
    dataset = SolarDataset(
        data_dir=str(DATA_DIR),
        metadata_csv=str(METADATA_CSV),
    )
    n_val = int(len(dataset) * VAL_SPLIT)
    n_train = len(dataset) - n_val
    generator = torch.Generator().manual_seed(SEED)
    train_ds, val_ds = random_split(dataset, [n_train, n_val], generator=generator)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
    return train_loader, val_loader, n_train, n_val


def count_parameters(model: nn.Module) -> int:
    """Count trainable parameters only."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device):
    """Evaluate a baseline and return MAE, RMSE, and R2 on the validation split."""
    model.eval()
    preds, targets = [], []
    with torch.no_grad():
        for images, labels in loader:
            # Collapse dual-channel (B+, B-) → single-channel |B| = B+ + B-.
            # SolarDataset always returns (N, 2, H, W); baselines require (N, 1, H, W).
            images_1ch = (images[:, 0:1, :, :] + images[:, 1:2, :, :]).to(device)
            out = model(images_1ch).squeeze(-1).cpu().numpy()
            preds.extend(out.tolist())
            targets.extend(labels.squeeze(-1).numpy().tolist())

    preds = np.array(preds)
    targets = np.array(targets)
    mae = float(mean_absolute_error(targets, preds))
    rmse = float(np.sqrt(mean_squared_error(targets, preds)))
    r2 = float(r2_score(targets, preds))
    return mae, rmse, r2


def measure_inference_time(model: nn.Module, device: torch.device) -> float:
    """Measure warm-start single-sample latency for a 512x512 magnetogram."""
    model.eval()
    dummy = torch.randn(1, 1, 512, 512, device=device)
    with torch.no_grad():
        for _ in range(INFERENCE_WARMUP):
            model(dummy)
        t0 = time.perf_counter()
        for _ in range(INFERENCE_RUNS):
            model(dummy)
        elapsed = time.perf_counter() - t0
    return elapsed / INFERENCE_RUNS * 1000


def train(model: nn.Module, train_loader: DataLoader, val_loader: DataLoader,
          device: torch.device) -> None:
    """Train one baseline with the fixed benchmark protocol."""
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            # Collapse dual-channel (B+, B-) → single-channel |B| = B+ + B-.
            images = (images[:, 0:1, :, :] + images[:, 1:2, :, :]).to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        if epoch % 10 == 0 or epoch == 1:
            mae, _, r2 = evaluate(model, val_loader, device)
            logger.info(
                f"    Epoch {epoch:02d}/{NUM_EPOCHS} | "
                f"Train Loss: {running_loss / len(train_loader):.4f} | "
                f"Val MAE: {mae:.4f} | R²: {r2:.4f}"
            )


# ── Model builders ────────────────────────────────────────────────────────────

def build_resnet18() -> nn.Module:
    """Adapt ResNet-18 from RGB classification to one-channel regression."""
    net = models.resnet18(weights=None)
    net.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
    net.fc = nn.Linear(net.fc.in_features, 1)
    return net


def build_vgg11() -> nn.Module:
    """Adapt VGG-11 to one-channel regression with MPS-safe global pooling."""
    net = models.vgg11(weights=None)
    net.features[0] = nn.Conv2d(1, 64, kernel_size=3, padding=1)
    # Implementation Detail: 512 px / 2^5 maxpools = 16 px spatial dim.
    # 16 % 7 ≠ 0 triggers an MPS division error; (1,1) is always divisible.
    net.avgpool = nn.AdaptiveAvgPool2d((1, 1))
    net.classifier = nn.Sequential(
        nn.Linear(512, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(0.5),
        nn.Linear(256, 1),
    )
    return net


# ── Naive Persistence ─────────────────────────────────────────────────────────

class NaivePersistence:
    """Lower-bound baseline that predicts the training-set mean."""

    def __init__(self):
        self.mean: float = 0.0

    def fit(self, train_loader: DataLoader) -> None:
        """Compute the only learned value for the constant baseline."""
        targets = [
            label.item()
            for _, labels in train_loader
            for label in labels.squeeze(-1)
        ]
        self.mean = float(np.mean(targets))
        logger.info(f"    Training mean: {self.mean:.6f}")

    def evaluate(self, val_loader: DataLoader):
        """Compute metrics against constant mean predictions."""
        targets = [
            label.item()
            for _, labels in val_loader
            for label in labels.squeeze(-1)
        ]
        targets = np.array(targets)
        preds = np.full_like(targets, self.mean)
        mae = float(mean_absolute_error(targets, preds))
        rmse = float(np.sqrt(mean_squared_error(targets, preds)))
        r2 = float(r2_score(targets, preds))
        return mae, rmse, r2

    def measure_inference_time(self) -> float:
        """Measure attribute-read latency for parity with model timing fields."""
        t0 = time.perf_counter()
        for _ in range(INFERENCE_RUNS):
            _ = self.mean
        return (time.perf_counter() - t0) / INFERENCE_RUNS * 1000


# ── Resume helper ─────────────────────────────────────────────────────────────

def _run_or_load(
    builder,
    weights_filename: str,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
) -> dict:
    """Resume an existing baseline checkpoint or train, then profile it."""
    weights_path = MODELS_DIR / weights_filename
    model = builder()
    n_params = count_parameters(model)
    logger.info(f"    Parameters: {n_params:,}")

    if weights_path.exists():
        logger.info(f"    Found existing weights, skipping training → {weights_path.relative_to(PROJECT_ROOT)}")
        model.load_state_dict(torch.load(weights_path, map_location=device))
        model.to(device)
    else:
        train(model, train_loader, val_loader, device)
        torch.save(model.state_dict(), weights_path)
        logger.info(f"    Weights → {weights_path.relative_to(PROJECT_ROOT)}")

    mae, rmse, r2 = evaluate(model, val_loader, device)
    inf_ms = measure_inference_time(model, device)
    logger.info(f"    MAE: {mae:.4f} | RMSE: {rmse:.4f} | R²: {r2:.4f} | Inference: {inf_ms:.2f} ms")

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "inference_time_ms": round(inf_ms, 2),
        "total_parameters": n_params,
        "weights_file": str(weights_path.relative_to(PROJECT_ROOT)),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """Run all baselines and persist the JSON consumed by the API."""
    set_seed(SEED)
    device = get_device()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Device   : {device}")
    logger.info(f"Epochs   : {NUM_EPOCHS}  |  LR: {LEARNING_RATE}  |  Batch: {BATCH_SIZE}")
    logger.info("Loading dataset...")
    train_loader, val_loader, n_train, n_val = build_dataloaders()
    logger.info(f"Samples  : {n_train} train / {n_val} val")

    results = {
        "run_id": "benchmarking_baselines",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": {
            "total_samples": n_train + n_val,
            "train_samples": n_train,
            "val_samples": n_val,
            "val_split": VAL_SPLIT,
        },
        "hyperparameters": {
            "epochs": NUM_EPOCHS,
            "learning_rate": LEARNING_RATE,
            "batch_size": BATCH_SIZE,
            "optimizer": "Adam",
            "seed": SEED,
        },
        "models": {},
    }

    # ── 1. Naive Persistence ──────────────────────────────────────────────────
    logger.info("\n=== [1/3] Naive Persistence ===")
    naive = NaivePersistence()
    naive.fit(train_loader)
    mae, rmse, r2 = naive.evaluate(val_loader)
    inf_ms = naive.measure_inference_time()
    logger.info(f"    MAE: {mae:.4f} | RMSE: {rmse:.4f} | R²: {r2:.4f} | Inference: {inf_ms:.4f} ms")

    results["models"]["naive_persistence"] = {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "inference_time_ms": round(inf_ms, 6),
        "total_parameters": 0,
        "weights_file": None,
    }

    # ── 2. ResNet-18 ──────────────────────────────────────────────────────────
    logger.info("\n=== [2/3] ResNet-18 ===")
    results["models"]["resnet18"] = _run_or_load(
        build_resnet18, "resnet18_baseline.pth",
        train_loader, val_loader, device,
    )

    # ── 3. VGG-11 ─────────────────────────────────────────────────────────────
    logger.info("\n=== [3/3] VGG-11 ===")
    results["models"]["vgg11"] = _run_or_load(
        build_vgg11, "vgg11_baseline.pth",
        train_loader, val_loader, device,
    )

    # ── Save JSON ─────────────────────────────────────────────────────────────
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nResults saved → {RESULTS_PATH.relative_to(PROJECT_ROOT)}")

    logger.info("\n=== Benchmarking Summary ===")
    header = f"  {'Model':<22} {'MAE':>8} {'RMSE':>8} {'R²':>8} {'Params':>12} {'ms/inf':>8}"
    logger.info(header)
    logger.info("  " + "-" * (len(header) - 2))
    for name, m in results["models"].items():
        params = f"{m['total_parameters']:,}" if m["total_parameters"] else "—"
        logger.info(
            f"  {name:<22} {m['mae']:>8.4f} {m['rmse']:>8.4f} {m['r2']:>8.4f} "
            f"{params:>12} {m['inference_time_ms']:>8.2f}"
        )


if __name__ == "__main__":
    main()
