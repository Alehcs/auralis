"""Evaluate the promoted Coronium V3 PRO checkpoint on the hold-out split.

The output CSV feeds the research scatter plot and dashboard. Metrics remain in
log-SI space because that is the model's direct training target.
"""

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Keep train_model.py importable without installing the project as a package.
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent  # auralis-back/
sys.path.insert(0, str(ROOT / "src"))
from models.train_model import SolarDataset, CoroniumV3  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths are relative to the auralis-back/ working directory.
# ---------------------------------------------------------------------------
WEIGHTS_PATH  = Path("models/best_coronium_v3_pro_augmented.pth")
SCALER_PATH   = Path("models/target_scaler.json")
SPLIT_PATH    = Path("models/split_indices.json")
DATA_DIR      = Path("data/processed")
METADATA_CSV  = Path("data/processed/metadata_processed.csv")
REPORT_CSV    = Path("reports/results_comparison.csv")

# Must match train_model.main().
VAL_SPLIT    = 0.2
BATCH_SIZE   = 32
DROPOUT_RATE = 0.2

# Reproducibility — fix all RNG sources so MC Dropout masks are deterministic.
# This guarantees that re-running this script yields identical metrics every
# time, which is required for citation in a thesis / conference proceedings.
SEED = 42
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
if torch.backends.mps.is_available():
    torch.mps.manual_seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_device() -> torch.device:
    """Select the fastest available backend for evaluation."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Backend: CUDA — %s", torch.cuda.get_device_name(0))
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Backend: MPS (Apple Silicon)")
    else:
        device = torch.device("cpu")
        logger.info("Backend: CPU")
    return device


def load_scaler(scaler_path: Path) -> tuple[float, float]:
    """Read scaler metadata written during preprocessing."""
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Scaler not found: {scaler_path}\n"
            "Run prepare_dataset.py with normalize_sunspot_targets() before evaluation."
        )
    with open(scaler_path) as f:
        data = json.load(f)
    mean: float = float(data["mean"])
    std: float  = float(data["std"])
    logger.info("Scaler loaded: mean=%.4f  std=%.4f", mean, std)
    return mean, std


def build_val_loader() -> DataLoader:
    """Rebuild the exact validation split used during training.

    The preferred path loads ``models/split_indices.json`` written by
    ``train_model.py`` so evaluation uses the same hold-out samples. The
    chronological split fallback exists only for old checkpoints created before
    split persistence was added.
    """
    full_dataset = SolarDataset(
        data_dir=str(DATA_DIR),
        metadata_csv=str(METADATA_CSV),
        transform=None,
    )
    total = len(full_dataset)

    if SPLIT_PATH.exists():
        with open(SPLIT_PATH) as f:
            split_data = json.load(f)
        val_indices = split_data["val"]
        logger.info(
            "Loaded split indices from %s: %d validation samples",
            SPLIT_PATH, len(val_indices),
        )
    else:
        logger.warning(
            "split_indices.json not found at %s; falling back to chronological split. "
            "Retrain with train_model.py to generate the random split.",
            SPLIT_PATH,
        )
        val_n   = int(total * VAL_SPLIT)
        train_n = total - val_n
        val_indices = list(range(train_n, total))

    val_subset = Subset(full_dataset, val_indices)
    logger.info("Validation split: %d samples out of %d total", len(val_subset), total)

    return DataLoader(val_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)


def run_inference(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Run MC Dropout while keeping BatchNorm fixed in eval mode."""
    T = 20
    model.eval()  # Freeze BatchNorm running stats.
    for m in model.modules():
        if m.__class__.__name__.startswith('Dropout'):
            m.train()  # Re-enable only Dropout for MC sampling.
    y_real_list, y_pred_list = [], []

    with torch.no_grad():
        for images, targets in tqdm(loader, desc="MC inference", unit="batch"):
            images = images.to(device)
            preds = torch.stack([model(images) for _ in range(T)])  # (T, B, 1)
            outputs = preds.mean(dim=0)                              # (B, 1)
            y_pred_list.extend(outputs.squeeze(1).cpu().numpy())
            y_real_list.extend(targets.squeeze(1).numpy())

    return np.array(y_real_list), np.array(y_pred_list)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(y_real: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute regression metrics; MAPE skips zero targets."""
    residuals = y_pred - y_real

    mae  = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    # R2 = 1 - SS_res / SS_tot.
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_real - y_real.mean()) ** 2))
    r2     = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else float("nan")

    # MAPE only on samples with nonzero target activity.
    nonzero_mask = y_real != 0.0
    if nonzero_mask.sum() > 0:
        mape = float(np.mean(np.abs(residuals[nonzero_mask] / y_real[nonzero_mask])) * 100)
    else:
        mape = float("nan")

    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


def print_thesis_report(metrics: dict, n_samples: int, mean: float, std: float) -> None:
    """Print a compact evaluation report for reports and thesis figures."""
    sep = "=" * 62
    print(f"\n{sep}")
    print("  Coronium V3 PRO + ExtremeAugmentation - Final Evaluation Report")
    print(sep)
    print(f"  Samples evaluated  : {n_samples:>8,}")
    print(f"  MAE                : {metrics['mae']:>10.4f}  [log-SI]")
    print(f"  RMSE               : {metrics['rmse']:>10.4f}  [log-SI]")
    print(f"  R2                 : {metrics['r2']:>10.4f}  [-]")
    print(f"  MAPE               : {metrics['mape']:>10.2f}  [%]  (excludes y=0)")
    print(sep)
    print("  Scale: log(SI), the model's direct training target")
    print(f"  Scaler reference: mean={mean:.4f}  std={std:.4f}; no transform applied")
    print(sep + "\n")


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_comparison_csv(
    y_real: np.ndarray,
    y_pred: np.ndarray,
    output_path: Path,
) -> None:
    """Write the dashboard scatter-plot CSV using its existing column names."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "Real_SSN":       np.round(y_real, 6),
        "Predicted_SSN":  np.round(y_pred, 6),
        "Error_Absoluto": np.round(np.abs(y_pred - y_real), 6),
    })

    df.to_csv(output_path, index=False)
    logger.info("CSV exported: %s (%d rows)", output_path, len(df))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run final evaluation and refresh the dashboard comparison CSV."""
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {WEIGHTS_PATH}\n"
            "Run train_model.py first to generate the weights."
        )

    # Load scaler only as provenance metadata; metrics stay in log-SI space.
    mean, std = load_scaler(SCALER_PATH)

    device = get_device()

    model = CoroniumV3(in_channels=2, dropout_rate=DROPOUT_RATE)
    state = torch.load(WEIGHTS_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.to(device)
    logger.info("Weights loaded from %s", WEIGHTS_PATH)

    val_loader = build_val_loader()

    y_real_norm, y_pred_norm = run_inference(model, val_loader, device)

    # Direct log-SI comparison. SolarDataset already returns the target in the
    # same space the model learned, so no additional transform is applied.
    y_real = y_real_norm   # log(SI) real
    y_pred = y_pred_norm   # predicted log(SI)

    metrics = compute_metrics(y_real, y_pred)
    print_thesis_report(metrics, n_samples=len(y_real), mean=mean, std=std)

    export_comparison_csv(y_real, y_pred, REPORT_CSV)


if __name__ == "__main__":
    main()
