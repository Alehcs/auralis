"""Scatter-plot evaluation of CoroniumV3 PRO on the validation set.

Loads the final checkpoint, runs a clean (no-dropout, no-augmentation) forward
pass over the held-out 20 % validation split, and saves a Predicted vs. Real
scatter plot to reports/figures/error_scatter.png.

Usage (from repo root):
    python auralis-back/src/models/evaluate_model.py
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.utils.data import DataLoader, Subset
from tqdm import tqdm

# Reuse all dataset / model definitions from the training pipeline.
from train_model import SolarDataset, CoroniumV3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths (relative to the directory where you launch the script) ─────────────
WEIGHTS_PATH    = Path("models/coronium_v3_pro.pth")
DATA_DIR        = Path("data/processed")
METADATA_CSV    = Path("data/processed/metadata_processed.csv")
OUTPUT_PATH     = Path("reports/figures/error_scatter.png")

# ── Hyper-params must match train_model.main() exactly ───────────────────────
VAL_SPLIT    = 0.2
BATCH_SIZE   = 32
DROPOUT_RATE = 0.2

# ── Población Z-Score scaler (from models/target_scaler.json) ─────────────────
# Targets in SolarDataset are raw physical scale; model output is Z-score space.
# Inverse transform: y_physical = y_norm * SCALER_STD + SCALER_MEAN
SCALER_MEAN = 1.7658
SCALER_STD  = 0.3462


def build_val_loader() -> DataLoader:
    """Reconstruct the identical validation split used during training.

    Uses the same deterministic index slice (last VAL_SPLIT fraction) and
    no augmentation, mirroring the val_dataset_full / val_dataset construction
    in train_model.main().
    """
    full_dataset = SolarDataset(
        data_dir=str(DATA_DIR),
        metadata_csv=str(METADATA_CSV),
        transform=None,  # no augmentation for evaluation
    )
    total_size = len(full_dataset)
    val_size   = int(total_size * VAL_SPLIT)
    train_size = total_size - val_size

    val_indices = list(range(train_size, total_size))
    val_dataset = Subset(full_dataset, val_indices)

    logger.info("Validation samples: %d / %d total", len(val_dataset), total_size)
    return DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)


def run_inference(model: torch.nn.Module, loader: DataLoader, device: torch.device):
    """Collect ground-truth targets and model predictions for the full loader.

    Returns:
        targets (np.ndarray): shape (N,), real sunspot index values.
        preds   (np.ndarray): shape (N,), predicted sunspot index values.
    """
    model.eval()
    all_targets, all_preds = [], []

    with torch.no_grad():
        for images, targets in tqdm(loader, desc="Evaluating", unit="batch"):
            images  = images.to(device)
            outputs = model(images)          # (B, 1)
            all_preds.extend(outputs.squeeze(1).cpu().numpy())
            all_targets.extend(targets.squeeze(1).cpu().numpy())

    return np.array(all_targets), np.array(all_preds)


def plot_scatter(targets: np.ndarray, preds: np.ndarray, output_path: Path) -> None:
    """Save a Predicted vs. Real scatter plot with a perfect-fit reference line.

    Args:
        targets:     Array of ground-truth sunspot index values.
        preds:       Array of model predictions aligned with targets.
        output_path: Destination .png file (parent directory is created if needed).
    """
    mae  = np.mean(np.abs(preds - targets))
    rmse = np.sqrt(np.mean((preds - targets) ** 2))

    # Fixed axis limits matching the physical sunspot index range [1.0, 3.0].
    # Both arrays must already be in physical scale before calling this function.
    axis_min = 1.0
    axis_max = 3.0

    fig, ax = plt.subplots(figsize=(7, 7))

    ax.scatter(
        targets, preds,
        alpha=0.45, s=18, color="#1f77b4", edgecolors="none",
        label=f"Val samples (n={len(targets):,})",
    )

    # Perfect-fit diagonal y = x
    ax.plot(
        [axis_min, axis_max], [axis_min, axis_max],
        color="red", linestyle="--", linewidth=1.5, label="Perfect fit (y = x)",
    )

    ax.set_xlim(axis_min, axis_max)
    ax.set_ylim(axis_min, axis_max)
    ax.set_aspect("equal")

    ax.set_xlabel("Real (Sunspot Index)", fontsize=13)
    ax.set_ylabel("Predicted (Sunspot Index)", fontsize=13)
    ax.set_title("CoroniumV3 PRO — Predicted vs. Real\n(Validation Set)", fontsize=14)

    stats_text = f"MAE  = {mae:.4f}\nRMSE = {rmse:.4f}"
    ax.text(
        0.04, 0.95, stats_text,
        transform=ax.transAxes, fontsize=11, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="grey", alpha=0.8),
    )

    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Scatter plot saved → %s", output_path)


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    # ── Load model ────────────────────────────────────────────────────────────
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {WEIGHTS_PATH}\n"
            "Run train_model.py first to generate the weights file."
        )

    model = CoroniumV3(in_channels=2, dropout_rate=DROPOUT_RATE)
    model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device))
    model.to(device)
    logger.info("Weights loaded from %s", WEIGHTS_PATH)

    # ── Build validation DataLoader ───────────────────────────────────────────
    val_loader = build_val_loader()

    # ── Inference ─────────────────────────────────────────────────────────────
    targets, preds = run_inference(model, val_loader, device)

    # targets viene en escala física cruda desde SolarDataset — no se toca.
    # Solo las predicciones salen del modelo en espacio Z-Score y se desnormalizan.
    targets_physical = targets
    preds_physical   = preds * SCALER_STD + SCALER_MEAN

    logger.info(
        "Inference complete — MAE: %.4f | RMSE: %.4f",
        np.mean(np.abs(preds_physical - targets_physical)),
        np.sqrt(np.mean((preds_physical - targets_physical) ** 2)),
    )

    # ── Plot ──────────────────────────────────────────────────────────────────
    plot_scatter(targets_physical, preds_physical, OUTPUT_PATH)


if __name__ == "__main__":
    main()
