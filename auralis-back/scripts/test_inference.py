"""Compare high-activity inference between two Coronium V3 PRO checkpoints.

This regression check focuses on validation samples with ``sunspot_index > 2.0``
to verify whether targeted augmentation improved storm-like cases.
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from typing import List

# ---------------------------------------------------------------------------
# Make src/ importable so train_model resolves without package install
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent  # auralis-back/
sys.path.insert(0, str(ROOT / "src"))

from models.train_model import CoroniumV3             # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger("auralis.test_inference")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_ORIGINAL  = ROOT / "models" / "best_coronium_v3_pro.pth"
MODEL_AUGMENTED = ROOT / "models" / "best_coronium_v3_pro_augmented.pth"
DATA_DIR        = ROOT / "data"   / "processed"
METADATA_CSV    = DATA_DIR / "metadata_processed.csv"

EXTREME_THRESHOLD = 2.0


def load_image(data_dir: Path, filename: str) -> np.ndarray:
    img = np.load(str(data_dir / filename))
    if img.ndim == 2:
        b_pos = np.maximum(0.0, img)
        b_neg = np.maximum(0.0, -img)
        img = np.stack([b_pos, b_neg], axis=0).astype(np.float32)
    return img.astype(np.float32)


def load_model(path: Path) -> CoroniumV3:
    model = CoroniumV3(in_channels=2, dropout_rate=0.2)
    model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    model.eval()
    return model


def run_inference(model: CoroniumV3, rows: pd.DataFrame) -> List[dict]:
    results = []
    with torch.no_grad():
        for _, row in rows.iterrows():
            raw_fname = str(row["processed_file"])
            fname = (str(row["filename"]) + "_processed.npy"
                     if raw_fname.startswith("(") else raw_fname)
            img    = load_image(DATA_DIR, fname)
            tensor = torch.from_numpy(img).unsqueeze(0)
            pred   = model(tensor).item()
            real   = float(row["sunspot_index"])
            results.append({
                "filename":  fname[:50],
                "real":      real,
                "predicted": pred,
                "abs_error": abs(pred - real),
            })
    return results


def print_table(title: str, checkpoint: str, results: List[dict]) -> float:
    col_w   = 52
    header  = f"{'Image ID':<{col_w}}  {'Real':>8}  {'Predicted':>10}  {'Abs Error':>10}"
    divider = "-" * len(header)
    mae     = float(np.mean([r["abs_error"] for r in results]))

    print()
    print("=" * len(header))
    print(f"  {title}")
    print(f"  Checkpoint : {checkpoint}")
    print(f"  Samples    : {len(results)} extreme cases (sunspot_index > {EXTREME_THRESHOLD})")
    print("=" * len(header))
    print(header)
    print(divider)
    for r in results:
        print(f"{r['filename']:<{col_w}}  {r['real']:>8.4f}  "
              f"{r['predicted']:>10.4f}  {r['abs_error']:>10.4f}")
    print(divider)
    print(f"{'MAE on extreme samples':>{col_w + 2}}  {'':>8}  {'':>10}  {mae:>10.4f}")
    print("=" * len(header))
    return mae


def main() -> None:
    # The historical split is positional, matching the training script that
    # produced the two checkpoints being compared here.
    meta      = pd.read_csv(METADATA_CSV)
    val_start = int(len(meta) * 0.8)
    val_meta  = meta.iloc[val_start:].reset_index(drop=True)
    extremes  = val_meta[val_meta["sunspot_index"] > EXTREME_THRESHOLD].reset_index(drop=True)

    logger.info("Validation split: %d total | %d extreme samples (index > %.1f)",
                len(val_meta), len(extremes), EXTREME_THRESHOLD)

    mae_original = None
    if MODEL_ORIGINAL.exists():
        logger.info("Loading original checkpoint: %s", MODEL_ORIGINAL.name)
        model_orig   = load_model(MODEL_ORIGINAL)
        results_orig = run_inference(model_orig, extremes)
        mae_original = print_table(
            "ORIGINAL MODEL — No ExtremeAugmentation",
            MODEL_ORIGINAL.name, results_orig,
        )
    else:
        logger.warning("Original checkpoint not found: %s", MODEL_ORIGINAL)

    mae_augmented = None
    if MODEL_AUGMENTED.exists():
        logger.info("Loading augmented checkpoint: %s", MODEL_AUGMENTED.name)
        model_aug    = load_model(MODEL_AUGMENTED)
        results_aug  = run_inference(model_aug, extremes)
        mae_augmented = print_table(
            "AUGMENTED MODEL — ExtremeAugmentation threshold 2.0",
            MODEL_AUGMENTED.name, results_aug,
        )
    else:
        logger.warning("Augmented checkpoint not found: %s", MODEL_AUGMENTED)

    if mae_original is not None and mae_augmented is not None:
        delta    = mae_original - mae_augmented
        pct      = delta / mae_original * 100
        improved = "IMPROVED" if delta > 0 else "NO IMPROVEMENT"
        print()
        print("-" * 60)
        print("  FINAL COMPARISON — MAE ON EXTREME SAMPLES")
        print("-" * 60)
        print(f"  Original  (no aug) : {mae_original:.4f}")
        print(f"  Augmented (aug)    : {mae_augmented:.4f}")
        print(f"  Difference         : {delta:+.4f}  ({pct:+.1f}%)  {improved}")
        print("-" * 60)
        print()


if __name__ == "__main__":
    main()
