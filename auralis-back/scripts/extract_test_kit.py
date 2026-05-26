"""Export fixed demo PNGs for representative activity levels.

The selection uses the full processed metadata table, not just the validation
split, so the frontend has stable quiet, moderate, and extreme examples.

Run from ``auralis-back/``:
    python scripts/extract_test_kit.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Paths are resolved from the repository layout so the script can be run from
# ``auralis-back/`` without installing the package.
BASE_DIR      = Path(__file__).resolve().parent.parent          # auralis-back/
METADATA_CSV  = BASE_DIR / "data" / "processed" / "metadata_processed.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DEMO_DIR      = BASE_DIR.parent / "demo_assets"

# Target SI by category. ``None`` means the sample is selected by exact ID.
TARGETS = {
    "normal":   0.2,    # quiet Sun; expected to classify as low activity
    "moderate": 1.3,    # intermediate activity; expected to classify as medium
    "extreme":  None,   # fixed ID below
}

EXTREME_ID = "hmi.m_45s.2025.01.20_00_01_30_TAI"


def find_by_target(df: pd.DataFrame, target_ssn: float) -> pd.Series:
    """Return the row whose ``sunspot_index`` is closest to the target value."""
    idx = (df["sunspot_index"] - target_ssn).abs().idxmin()
    return df.loc[idx]


def find_by_id(df: pd.DataFrame, partial_id: str) -> pd.Series:
    """Return the row whose source filename contains the fixed sample ID."""
    matches = df[df["filename"].str.contains(partial_id, na=False)]
    if matches.empty:
        raise ValueError(
            f"No metadata row contains ID '{partial_id}'.\n"
            f"Check that the matching .npy file exists in {PROCESSED_DIR}."
        )
    return matches.iloc[0]


def npy_to_image(npy_path: Path, out_path: Path) -> None:
    """Render a processed magnetogram tensor as a frontend-ready PNG."""
    data = np.load(npy_path)

    if data.ndim == 3:
        # Dual-channel tensors store positive and negative polarity separately.
        mag = data[0] - data[1]
    else:
        # Legacy single-channel tensors are already signed and normalized.
        mag = data

    fig, ax = plt.subplots(figsize=(5.12, 5.12), dpi=100)
    ax.imshow(mag, cmap="RdBu_r", vmin=-1.0, vmax=1.0, origin="lower")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0, dpi=100)
    plt.close(fig)


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    # Use all processed metadata so sample selection remains independent from
    # whichever split was used for the latest training run.
    df = pd.read_csv(METADATA_CSV)

    print("\n  Coronium V3 PRO - Golden Sample Extractor")
    print(f"  Full dataset: {len(df):,} samples")
    print(f"  sunspot_index range: [{df['sunspot_index'].min():.4f}, {df['sunspot_index'].max():.4f}]")
    print("  " + "-" * 54)

    for category, target_ssn in TARGETS.items():
        if target_ssn is None:
            row = find_by_id(df, EXTREME_ID)
        else:
            row = find_by_target(df, target_ssn)

        sample_id = row["filename"]
        real_ssn  = row["sunspot_index"]
        npy_path  = PROCESSED_DIR / row["processed_file"]

        if not npy_path.exists():
            print(f"  [ERROR] File not found: {npy_path}")
            continue

        out_png = DEMO_DIR / f"test_{category}.png"
        npy_to_image(npy_path, out_png)

        delta = f"  (delta={abs(real_ssn - target_ssn):.4f} from target {target_ssn})" if target_ssn else ""
        print(
            f"  [{category.upper():8}]  ID: {sample_id}\n"
            f"             sunspot_index: {real_ssn:.4f}{delta}\n"
            f"             -> {out_png.relative_to(DEMO_DIR.parent)}\n"
        )

    print("  Done. Demo PNGs exported to demo_assets/.\n")


if __name__ == "__main__":
    main()
