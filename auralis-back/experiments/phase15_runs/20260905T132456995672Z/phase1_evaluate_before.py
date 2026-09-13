"""Evaluate a versioned run, or explicitly reproduce the contaminated legacy split.

Targets are SI pixel percentages, without log or Z-score. Legacy reproduction
is diagnostic only and never refreshes the dashboard's preserved report.
"""

import argparse
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
from processing.scientific_split import load_split, sha256
from processing.model_input import INPUT_CONTRACT, TARGET_CONTRACT

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
SPLIT_PATH    = Path("models/split_indices_phase1_v1.json")
DATA_DIR      = Path("data/processed")
METADATA_CSV  = Path("data/processed/metadata_processed.csv")
REPORT_CSV    = Path("reports/phase1_evaluation/results_comparison.csv")

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
            "This is historical metadata; do not regenerate or apply it to the promoted checkpoint."
        )
    with open(scaler_path) as f:
        data = json.load(f)
    mean: float = float(data["mean"])
    std: float  = float(data["std"])
    logger.info("Scaler loaded: mean=%.4f  std=%.4f", mean, std)
    return mean, std


def build_val_loader(split_path: Path = SPLIT_PATH, legacy_reproduction: bool = False) -> DataLoader:
    """Require an explicit persisted split; no positional fallback."""
    full_dataset = SolarDataset(data_dir=str(DATA_DIR), metadata_csv=str(METADATA_CSV), transform=None)
    if legacy_reproduction:
        if split_path.resolve() != Path("models/split_indices.json").resolve():
            raise ValueError("Legacy reproduction requires the original split")
        # Bind the original split, CSV and weights to the Phase 1 evidence.
        evidence = json.loads(Path("reports/phase1_v1/evidence.json").read_text())
        for path in (split_path, METADATA_CSV, WEIGHTS_PATH):
            if sha256(path) != evidence["preserved_artifact_sha256"][str(path)]:
                raise ValueError(f"Legacy artifact changed: {path}")
        split = json.loads(split_path.read_text())
        logger.warning("HISTORICAL DIAGNOSTIC: 145 overlapping observations; not independent validation")
    else:
        split = load_split(split_path, METADATA_CSV)
    return DataLoader(Subset(full_dataset, split["val"]), batch_size=BATCH_SIZE,
                      shuffle=False, num_workers=0)


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


def print_thesis_report(metrics: dict, n_samples: int, mean: float = 0.0, std: float = 1.0) -> None:
    """Print a compact evaluation report for reports and thesis figures."""
    sep = "=" * 62
    print(f"\n{sep}")
    print("  Coronium V3 PRO + ExtremeAugmentation - Evaluation Report (see provenance manifest)")
    print(sep)
    print(f"  Samples evaluated  : {n_samples:>8,}")
    print(f"  MAE                : {metrics['mae']:>10.4f}  [SI percentage points]")
    print(f"  RMSE               : {metrics['rmse']:>10.4f}  [SI percentage points]")
    print(f"  R2                 : {metrics['r2']:>10.4f}  [-]")
    print(f"  MAPE               : {metrics['mape']:>10.2f}  [%]  (excludes y=0)")
    print(sep)
    print("  Target: 100 * count(abs(B_LOS) > 200 G) / original image pixel count")
    print("  No logarithm or Z-score; target_scaler.json is not applied")
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

    df.to_csv(output_path, index=False, mode="x")
    logger.info("CSV exported: %s (%d rows)", output_path, len(df))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-reproduction", action="store_true")
    parser.add_argument("--run-dir", type=Path, help="Completed versioned training run")
    parser.add_argument("--output-dir", type=Path, default=REPORT_CSV.parent)
    args = parser.parse_args()
    if args.legacy_reproduction and args.run_dir:
        parser.error("Choose a versioned run OR explicit legacy reproduction")
    if args.legacy_reproduction:
        weights = WEIGHTS_PATH
        split_path = Path("models/split_indices.json")
        status = "historical_contaminated_validation_diagnostic_only"
    elif args.run_dir:
        weights = args.run_dir / "best.pth"
        manifest = json.loads((args.run_dir / "manifest.json").read_text())
        split_path = SPLIT_PATH
        if (manifest.get("status") != "completed_unpromoted"
                or manifest.get("checkpoint_sha256") != sha256(weights)
                or manifest.get("split_sha256") != sha256(split_path)
                or manifest.get("input_contract") != INPUT_CONTRACT
                or manifest.get("target_contract") != TARGET_CONTRACT):
            raise ValueError("Checkpoint provenance does not match this scientific contract/split")
        status = "deduplicated_observation_validation_not_temporal_validation"
    else:
        parser.error("Retraining required: use --run-dir; --legacy-reproduction is diagnostic only")

    val_loader = build_val_loader(split_path, args.legacy_reproduction)
    # Reserve a fresh directory BEFORE inference. Never overwrite old results.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    provenance = {"status": status, "weights_sha256": sha256(weights),
                  "split_sha256": sha256(split_path), "metadata_sha256": sha256(METADATA_CSV),
                  "input_contract": INPUT_CONTRACT, "target_contract": TARGET_CONTRACT,
                  "seed": SEED, "mc_passes": 20, "batch_size": BATCH_SIZE}
    (args.output_dir / "manifest.json").write_text(json.dumps(provenance, indent=2))
    device = get_device()
    model = CoroniumV3(in_channels=2, dropout_rate=DROPOUT_RATE)
    model.load_state_dict(torch.load(weights, map_location=device, weights_only=True))
    model.to(device)
    y_real, y_pred = run_inference(model, val_loader, device)
    metrics = compute_metrics(y_real, y_pred)
    print_thesis_report(metrics, n_samples=len(y_real))
    export_comparison_csv(y_real, y_pred, args.output_dir / "results_comparison.csv")
    provenance.update(metrics=metrics, device=str(device), torch_version=torch.__version__,
                      evaluation_completed=True)
    (args.output_dir / "manifest.json").write_text(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
