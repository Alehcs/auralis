"""Diagnostic plot for raw FITS data versus processed V3 PRO tensors.

The processed tensor stores positive and negative polarity separately. For
display only, the script reconstructs the symlog-domain magnetic magnitude as
``|B| = B+ + B-`` and plots it beside the original HMI frame.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sunpy.map


# ── Path resolution ────────────────────────────────────────────────────────────
# src/tools/visualize_tensor.py  ->  ../../  ->  auralis-back/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def find_first_fits(raw_dir: Path) -> Path:
    """Return the first .fits file found in *raw_dir* (sorted, deterministic)."""
    fits_files = sorted(raw_dir.glob("*.fits"))
    if not fits_files:
        raise FileNotFoundError(
            f"No .fits files found in {raw_dir}.\n"
            "Run the ingestion pipeline first:  python src/ingestion/massive_ingest_pipeline.py"
        )
    return fits_files[0]


def resolve_processed_path(fits_path: Path, processed_dir: Path) -> Path:
    """Derive the expected .npy path from the FITS stem.

    Convention established by prepare_dataset.py:
        <stem>.fits  ->  <stem>_processed.npy
    """
    expected = processed_dir / f"{fits_path.stem}_processed.npy"
    if not expected.exists():
        raise FileNotFoundError(
            f"Processed tensor not found: {expected}\n"
            "Run the preprocessing pipeline first:  python src/processing/prepare_dataset.py"
        )
    return expected


def print_stats(label: str, array: np.ndarray) -> None:
    """Print min / max / mean for *array* with a labelled header."""
    print(f"\n{'─'*50}")
    print(f"  {label}")
    print(f"{'─'*50}")
    print(f"  shape : {array.shape}")
    print(f"  dtype : {array.dtype}")
    print(f"  min   : {array.min():.6f}")
    print(f"  max   : {array.max():.6f}")
    print(f"  mean  : {array.mean():.6f}")


def adjusted_vrange(data: np.ndarray, plow: float = 1.0, phigh: float = 99.0):
    """Compute vmin/vmax from percentiles to clip cosmetic outliers."""
    vmin = float(np.nanpercentile(data, plow))
    vmax = float(np.nanpercentile(data, phigh))
    return vmin, vmax


def main() -> None:
    # ── 1. Discover files ──────────────────────────────────────────────────────
    try:
        fits_path = find_first_fits(RAW_DIR)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        npy_path = resolve_processed_path(fits_path, PROCESSED_DIR)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"FITS   : {fits_path.name}")
    print(f"Tensor : {npy_path.name}")

    # ── 2. Load data ───────────────────────────────────────────────────────────
    solar_map = sunpy.map.Map(str(fits_path))
    raw_data: np.ndarray = np.nan_to_num(solar_map.data, nan=0.0)

    tensor: np.ndarray = np.load(str(npy_path))          # shape (2, 512, 512)
    b_pos: np.ndarray = tensor[0]                         # ReLU(x')  — positive polarity
    b_neg: np.ndarray = tensor[1]                         # ReLU(-x') — negative polarity
    magnitude: np.ndarray = b_pos + b_neg                 # |B| = |x'| (symlog domain)

    # ── 3. Console statistics ──────────────────────────────────────────────────
    print_stats(f"RAW FITS  [{solar_map.date.iso}]  (Gauss)", raw_data)
    print_stats(
        "PROCESSED TENSOR  |B| = B+ + B-  (symlog domain)",
        magnitude,
    )
    print(f"\n  B+ channel  →  min: {b_pos.min():.4f}  max: {b_pos.max():.4f}  "
          f"mean: {b_pos.mean():.4f}")
    print(f"  B- channel  →  min: {b_neg.min():.4f}  max: {b_neg.max():.4f}  "
          f"mean: {b_neg.mean():.4f}")
    print()

    # ── 4. Side-by-side plot ───────────────────────────────────────────────────
    vmin_raw, vmax_raw = adjusted_vrange(raw_data)
    vmin_mag, vmax_mag = adjusted_vrange(magnitude)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        f"HMI Magnetogram — {solar_map.date.iso}\n"
        f"FITS: {fits_path.name}",
        fontsize=10,
        y=1.01,
    )

    # Left: raw FITS
    im0 = axes[0].imshow(
        raw_data,
        cmap="gray",
        vmin=vmin_raw,
        vmax=vmax_raw,
        origin="lower",
        interpolation="none",
    )
    axes[0].set_title(
        f"Raw FITS  (gray)\n"
        f"vmin={vmin_raw:.0f} G  /  vmax={vmax_raw:.0f} G\n"
        f"shape: {raw_data.shape}",
        fontsize=9,
    )
    axes[0].set_xlabel("Pixels (original resolution)")
    axes[0].axis("off")
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04, label="Flux density [G]")

    # Right: processed tensor magnitude
    im1 = axes[1].imshow(
        magnitude,
        cmap="magma",
        vmin=vmin_mag,
        vmax=vmax_mag,
        origin="lower",
        interpolation="none",
    )
    axes[1].set_title(
        r"Processed tensor  $|B| = B^+ + B^-$  (magma)" + "\n"
        f"symlog domain  |  vmin={vmin_mag:.3f}  /  vmax={vmax_mag:.3f}\n"
        f"shape: {magnitude.shape}  (512×512 resampled)",
        fontsize=9,
    )
    axes[1].set_xlabel("Pixels (512 × 512)")
    axes[1].axis("off")
    fig.colorbar(
        im1, ax=axes[1], fraction=0.046, pad=0.04,
        label=r"$|B'|$ = sign(B)·log(1+|B|)  [symlog]",
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
