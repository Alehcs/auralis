#!/usr/bin/env python3
"""
run_external_baselines.py
=========================
Benchmarking of external baseline models for solar activity regression.

Models evaluated:
  1. Naive Persistence   — predicts training-set mean for every sample
  2. ResNet-18           — adapted to 1-channel input and scalar regression
  3. VGG-11              — adapted to 1-channel input and scalar regression

Protocol:
  - Dataset : SolarDataset (1,158 magnetograms, 80/20 split, seed=42)
  - Epochs  : 30
  - LR      : 0.001  (Adam, matching exp_003)
  - Batch   : 32

Output:
  - experiments/results_benchmarking.json  (MAE, RMSE, R², inference time, # params)
  - models/baselines/resnet18_baseline.pth
  - models/baselines/vgg11_baseline.pth
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
    """Fix global random state for PyTorch and NumPy.

    Args:
        seed: Integer seed applied to ``torch.manual_seed`` and
            ``numpy.random.seed`` to ensure deterministic data splits
            and weight initialisation across benchmark runs.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)


def get_device() -> torch.device:
    """Select the highest-performance available compute device.

    Priority order: Apple MPS (M-series GPU) → CUDA → CPU.

    Returns:
        A ``torch.device`` instance pointing to the selected backend.
    """
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_dataloaders():
    """Construct stratified train/validation DataLoaders from SolarDataset.

    Applies a deterministic 80/20 split (``VAL_SPLIT``) seeded by ``SEED``
    to guarantee reproducible dataset partitions across benchmark runs,
    matching the split used during primary SolarNet training.

    Returns:
        Tuple of ``(train_loader, val_loader, n_train, n_val)`` where loaders
        are configured with ``BATCH_SIZE`` and the appropriate shuffle policy.
    """
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
    """Count the total number of trainable parameters in a module.

    Args:
        model: Any ``nn.Module`` instance.

    Returns:
        Sum of ``numel()`` for all parameters with ``requires_grad=True``.
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device):
    """Evaluate a regression model and compute standard error metrics.

    Runs a full pass over ``loader`` in inference mode, then computes Mean
    Absolute Error, Root Mean Squared Error, and the coefficient of
    determination (R²) between predictions and ground-truth labels.

    Args:
        model: Trained ``nn.Module``; placed in eval mode internally.
        loader: DataLoader yielding ``(image, label)`` batches.
        device: Compute device for tensor placement.

    Returns:
        Tuple ``(mae, rmse, r2)`` of Python floats.
    """
    model.eval()
    preds, targets = [], []
    with torch.no_grad():
        for images, labels in loader:
            out = model(images.to(device)).squeeze(-1).cpu().numpy()
            preds.extend(out.tolist())
            targets.extend(labels.squeeze(-1).numpy().tolist())

    preds = np.array(preds)
    targets = np.array(targets)
    mae = float(mean_absolute_error(targets, preds))
    rmse = float(np.sqrt(mean_squared_error(targets, preds)))
    r2 = float(r2_score(targets, preds))
    return mae, rmse, r2


def measure_inference_time(model: nn.Module, device: torch.device) -> float:
    """Benchmark single-sample inference latency.

    Executes ``INFERENCE_WARMUP`` un-timed passes to saturate JIT caches
    and device pipelines, then averages ``INFERENCE_RUNS`` timed passes.
    Input shape matches production magnetograms: ``(1, 1, 512, 512)``.

    Args:
        model: Trained ``nn.Module`` in eval mode.
        device: Compute device for tensor placement.

    Returns:
        Mean inference time in milliseconds per sample.
    """
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
    """Train a model for ``NUM_EPOCHS`` with Adam optimiser and MSE loss.

    Logs validation MAE and R² at epoch 1 and every 10 epochs thereafter,
    matching the reporting cadence of the primary SolarNet training runs
    to allow direct comparison across experiments.

    Args:
        model: ``nn.Module`` to optimise; moved to ``device`` in-place.
        train_loader: DataLoader for the training partition.
        val_loader: DataLoader for the validation partition.
        device: Compute device for training.
    """
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
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
    """Instantiate ResNet-18 adapted for single-channel scalar regression.

    Replaces the standard 3-channel ``conv1`` with a 1-channel equivalent
    and substitutes the ImageNet classification head with a single linear
    unit to produce a continuous sunspot index estimate.

    Returns:
        Configured ``nn.Module`` with randomly initialised weights.
    """
    net = models.resnet18(weights=None)
    net.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
    net.fc = nn.Linear(net.fc.in_features, 1)
    return net


def build_vgg11() -> nn.Module:
    """Instantiate VGG-11 adapted for single-channel scalar regression.

    Two architectural modifications are applied:

    1. **Input adaptation**: ``features[0]`` is replaced with a 1-channel
       3×3 convolution to accept HMI magnetograms instead of RGB imagery.

    2. **MPS-compatible pooling**: The default ``AdaptiveAvgPool2d((7, 7))``
       maps a 16×16 spatial tensor (512 px / 2⁵ maxpools) onto a 7-wide
       grid (16 % 7 ≠ 0), raising a division error on Apple MPS.
       Replaced with ``AdaptiveAvgPool2d((1, 1))`` (global average pooling)
       followed by a lightweight 512 → 256 → 1 regression head.

    Returns:
        Configured ``nn.Module`` with randomly initialised weights.
    """
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
    """Lower-bound baseline that predicts the training-set mean unconditionally.

    Provides the theoretical performance floor for regression: any model
    failing to outperform this baseline on MAE/RMSE has not learned
    task-relevant features beyond dataset statistics.
    """

    def __init__(self):
        self.mean: float = 0.0

    def fit(self, train_loader: DataLoader) -> None:
        """Compute and store the training-label mean.

        Args:
            train_loader: DataLoader for the training partition; labels
                are expected as tensors of shape ``(N, 1)`` or ``(N,)``.
        """
        targets = [
            label.item()
            for _, labels in train_loader
            for label in labels.squeeze(-1)
        ]
        self.mean = float(np.mean(targets))
        logger.info(f"    Training mean: {self.mean:.6f}")

    def evaluate(self, val_loader: DataLoader):
        """Compute regression metrics against constant mean predictions.

        Args:
            val_loader: DataLoader for the validation partition.

        Returns:
            Tuple ``(mae, rmse, r2)`` of Python floats. R² is expected to
            be zero or negative for a well-distributed target distribution.
        """
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
        """Benchmark constant-prediction latency over ``INFERENCE_RUNS`` passes.

        Returns:
            Mean time in milliseconds per prediction (attribute lookup only).
        """
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
    """Train or restore a model, then evaluate and profile it.

    Checks ``MODELS_DIR / weights_filename`` before training; if the file
    exists, training is skipped and weights are loaded directly. Allows
    interrupted benchmark runs to resume without retraining.

    Args:
        builder: Zero-argument callable returning a fresh ``nn.Module``.
        weights_filename: Basename (no path) for persisting model weights.
        train_loader: DataLoader for the training partition.
        val_loader: DataLoader for the validation partition.
        device: Compute device for training and inference.

    Returns:
        Dictionary with keys ``mae``, ``rmse``, ``r2``, ``inference_time_ms``,
        ``total_parameters``, and ``weights_file``.
    """
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
    """Execute the full baseline benchmarking pipeline and persist results.

    Orchestrates dataset loading, model training (or weight restoration),
    evaluation, and inference profiling for three baselines: Naive
    Persistence, ResNet-18, and VGG-11. Aggregated metrics are written
    to ``RESULTS_PATH`` as a structured JSON document.
    """
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
