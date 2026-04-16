"""Recalculate target_scaler.json from the full processed dataset.

The sunspot_index (target) is not stored inside the .npy image tensors —
it lives in data/processed/metadata_processed.csv under the column
'sunspot_index_raw' (the pre-normalisation value). This script:

    1. Discovers all .npy files present in data/processed/.
    2. Looks up the corresponding sunspot_index_raw in the CSV for each file.
    3. Computes mean and std over the matched population.
    4. Overwrites models/target_scaler.json with the new values.

Usage (run from HeliosPipeline/):
    python recalculate_scaler.py
    python recalculate_scaler.py --processed-dir data/processed \
                                  --csv data/processed/metadata_processed.csv \
                                  --scaler models/target_scaler.json
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def recalculate_scaler(
    processed_dir: str = "data/processed",
    csv_path: str = "data/processed/metadata_processed.csv",
    scaler_path: str = "models/target_scaler.json",
) -> None:
    processed = Path(processed_dir)
    csv_file = Path(csv_path)
    scaler_file = Path(scaler_path)

    # ── 1. Collect .npy files present on disk ────────────────────────────────
    npy_files = sorted(processed.glob("*.npy"))
    if not npy_files:
        raise FileNotFoundError(f"No .npy files found in {processed.absolute()}")
    logger.info("Found %d .npy files in %s", len(npy_files), processed)

    # ── 2. Load metadata CSV ──────────────────────────────────────────────────
    if not csv_file.exists():
        raise FileNotFoundError(
            f"Metadata CSV not found: {csv_file.absolute()}\n"
            "Run prepare_dataset.py first, or point --csv at the correct path."
        )
    df = pd.read_csv(csv_file)

    if "processed_file" not in df.columns:
        raise KeyError("CSV is missing the 'processed_file' column.")

    # Resolve target column: prefer sunspot_index_raw (post-normalize pipeline);
    # fall back to sunspot_index (older pipeline that stored raw values directly).
    if "sunspot_index_raw" in df.columns:
        target_col = "sunspot_index_raw"
    elif "sunspot_index" in df.columns:
        target_col = "sunspot_index"
        # Sanity-check: Z-score normalised values cluster tightly around 0.
        # Raw sunspot indices are typically >> 0.5, so warn only if it looks normalised.
        sample_mean = df[target_col].mean()
        if abs(sample_mean) < 0.1:
            logger.warning(
                "'sunspot_index_raw' not found and 'sunspot_index' mean=%.4f looks "
                "Z-score normalised — scaler will be computed on normalised values, "
                "which is likely wrong. Re-run prepare_dataset.py to regenerate the CSV.",
                sample_mean,
            )
        else:
            logger.info(
                "Using 'sunspot_index' as target (mean=%.4f — looks like raw values).",
                sample_mean,
            )
    else:
        raise KeyError("CSV has neither 'sunspot_index_raw' nor 'sunspot_index' column.")

    logger.info("Target column: '%s'", target_col)

    # ── 3. Deduplicate CSV and match .npy filenames ───────────────────────────
    # The CSV may contain multiple rows per file when the pipeline was run
    # more than once. Keep the last occurrence (most recent run).
    n_before = len(df)
    df_dedup = df.drop_duplicates(subset="processed_file", keep="last")
    n_dropped = n_before - len(df_dedup)
    if n_dropped:
        logger.info(
            "CSV had %d duplicate rows — kept last occurrence of each file (%d unique).",
            n_dropped, len(df_dedup),
        )

    csv_index = df_dedup.set_index("processed_file")[target_col]

    targets = []
    missing = []
    for npy in npy_files:
        key = npy.name
        if key in csv_index.index:
            targets.append(float(csv_index[key]))
        else:
            missing.append(key)

    if missing:
        logger.warning(
            "%d .npy files have no matching row in the CSV (skipped):\n  %s",
            len(missing),
            "\n  ".join(missing[:10]) + (" …" if len(missing) > 10 else ""),
        )

    if not targets:
        raise ValueError(
            "No targets could be matched. "
            "Check that 'processed_file' values in the CSV match the .npy filenames."
        )

    # ── 4. Compute population statistics ─────────────────────────────────────
    values = np.array(targets, dtype=np.float64)
    mean = float(values.mean())
    std = float(values.std())

    if std == 0.0:
        raise ValueError("std is 0 — all targets are identical; scaler is undefined.")

    logger.info("=" * 60)
    logger.info("Population  : %d samples", len(values))
    logger.info("Mean        : %.6f", mean)
    logger.info("Std         : %.6f", std)
    logger.info("Min / Max   : %.6f / %.6f", values.min(), values.max())
    logger.info("=" * 60)

    # ── 5. Overwrite scaler JSON ──────────────────────────────────────────────
    old_values = {}
    if scaler_file.exists():
        with open(scaler_file) as f:
            old_values = json.load(f)
        logger.info(
            "Previous scaler  mean=%.6f  std=%.6f  (computed from %s)",
            old_values.get("mean", float("nan")),
            old_values.get("std", float("nan")),
            scaler_file,
        )

    scaler_file.parent.mkdir(parents=True, exist_ok=True)
    with open(scaler_file, "w") as f:
        json.dump({"mean": mean, "std": std}, f, indent=2)

    logger.info("Scaler written: %s", scaler_file.absolute())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recalculate target_scaler.json")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing the processed .npy files (default: data/processed)",
    )
    parser.add_argument(
        "--csv",
        default="data/processed/metadata_processed.csv",
        help="Metadata CSV produced by prepare_dataset.py",
    )
    parser.add_argument(
        "--scaler",
        default="models/target_scaler.json",
        help="Output path for the scaler JSON (default: models/target_scaler.json)",
    )
    args = parser.parse_args()

    recalculate_scaler(
        processed_dir=args.processed_dir,
        csv_path=args.csv,
        scaler_path=args.scaler,
    )
