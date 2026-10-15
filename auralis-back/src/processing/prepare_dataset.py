"""Prepare a NEW clip400 dataset; SI = % original pixels with |B_LOS| > 200 G. Existing data never replaced."""

import csv
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import warnings

import numpy as np
import sunpy.map
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from processing.model_input import normalize_field, prepare_model_input
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


def log_scale(x: np.ndarray) -> np.ndarray:
    """Historical experimental transform; NOT used by the promoted checkpoint."""
    return np.sign(x) * np.log1p(np.abs(x))


def load_and_process_magnetogram(
    fits_path: Path,
    target_size: int = 512,
    sunspot_threshold: float = 200.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load one HMI FITS as a (2, N, N) clip400 B+/B- tensor plus metadata; SI uses pre-resample pixels."""
    try:
        solar_map = sunpy.map.Map(str(fits_path))
        data: np.ndarray = solar_map.data

        data = np.nan_to_num(data, nan=0.0)

        strong_field_mask: np.ndarray = np.abs(data) > sunspot_threshold
        sunspot_index: float = (np.sum(strong_field_mask) / data.size) * 100.0

        if target_size != 512 or sunspot_threshold != 200.0:
            raise ValueError("Promoted contract requires 512 px and a 200 G target threshold")
        processed = prepare_model_input(normalize_field(data, target_size))
        b_pos, b_neg = processed

        metadata: Dict[str, Any] = {
            "filename": fits_path.stem,
            "date": solar_map.date.iso,
            "date_scale": solar_map.date.scale.upper(),
            "date_source": "solar_map.date",
            "date_utc": solar_map.date.utc.isot + "Z",
            "sunspot_index": sunspot_index,
            "original_shape": data.shape,
            "processed_shape": processed.shape,
            "b_pos_max": float(np.max(b_pos)),
            "b_neg_max": float(np.max(b_neg)),
            "mean_b_pos": float(np.mean(b_pos)),
            "mean_b_neg": float(np.mean(b_neg)),
        }

        return processed.astype(np.float32), metadata

    except Exception as e:
        logger.error("Failed to process %s: %s", fits_path.name, e)
        raise


def prepare_dataset(
    raw_dir: str = "data/raw",
    processed_dir: str = "data/processed_phase1_v1",
    target_size: int = 512,
    sunspot_threshold: float = 200.0,
) -> List[Dict[str, Any]]:
    """Process sorted ``raw_dir`` FITS files into .npy tensors; per-file errors are logged and skipped."""
    processed_path = Path(processed_dir)
    if processed_path.exists() and any(processed_path.iterdir()):
        raise FileExistsError(f"Use a new dataset version; refusing to replace {processed_path}")
    processed_path.mkdir(parents=True, exist_ok=True)

    raw_path = Path(raw_dir)
    fits_files: List[Path] = sorted(raw_path.glob("*.fits"))

    if not fits_files:
        logger.warning("No FITS files found in %s", raw_dir)
        return []

    logger.info(
        "%d files to process  |  output: 2 x %dx%d px  |  scaling: clip400",
        len(fits_files), target_size, target_size,
    )

    all_metadata: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for fits_file in tqdm(fits_files, desc="Processing magnetograms", unit="file"):
        try:
            processed_data, metadata = load_and_process_magnetogram(
                fits_file,
                target_size=target_size,
                sunspot_threshold=sunspot_threshold,
            )

            output_filename = f"{fits_file.stem}_processed.npy"
            np.save(str(processed_path / output_filename), processed_data)

            metadata["processed_file"] = output_filename
            all_metadata.append(metadata)

        except Exception as e:
            logger.error("Skipping %s: %s", fits_file.name, e)
            errors.append({"filename": fits_file.name, "error": str(e)})

    logger.info("=" * 70)
    logger.info(
        "Complete  |  processed: %d  |  errors: %d  |  output: %s",
        len(all_metadata), len(errors), processed_path.absolute(),
    )
    logger.info("=" * 70)

    for err in errors:
        logger.warning("  %s: %s", err["filename"], err["error"])

    return all_metadata


def normalize_sunspot_targets(
    metadata_list: List[Dict[str, Any]],
    scaler_path: str = "models/target_scaler.json",
) -> Tuple[float, float]:
    """Historical Z-score helper for explicit experiments only; keeps raw SI as ``sunspot_index_raw``."""
    if not metadata_list:
        raise ValueError("metadata_list is empty — cannot fit scaler.")

    raw_values = np.array([m["sunspot_index"] for m in metadata_list], dtype=np.float64)
    mean: float = float(raw_values.mean())
    std: float = float(raw_values.std())

    if std == 0.0:
        raise ValueError(
            "sunspot_index has zero variance across the dataset — "
            "Z-Score normalisation is undefined."
        )

    for m in metadata_list:
        m["sunspot_index_raw"] = m["sunspot_index"]
        m["sunspot_index"] = (m["sunspot_index"] - mean) / std

    scaler_file = Path(scaler_path)
    scaler_file.parent.mkdir(parents=True, exist_ok=True)
    with open(scaler_file, "x") as f:
        json.dump({"mean": mean, "std": std}, f, indent=2)

    logger.info(
        "Target scaler saved: %s  |  mean=%.4f  std=%.4f",
        scaler_file.absolute(), mean, std,
    )
    return mean, std


def save_metadata_csv(
    metadata_list: List[Dict[str, Any]],
    output_path: str = "data/processed_phase1_v1/metadata_processed.csv",
) -> None:
    """Write metadata CSV, stringifying shape tuples for portability."""
    if not metadata_list:
        logger.warning("No metadata to write.")
        return

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "filename",
        "date",
        "date_scale",
        "date_source",
        "date_utc",
        "sunspot_index",        # Raw SI pixel percent (regression target)
        "sunspot_index_raw",    # Original value before normalisation
        "processed_file",
        "original_shape",
        "processed_shape",
        "b_pos_max",
        "b_neg_max",
        "mean_b_pos",
        "mean_b_neg",
    ]

    with open(output_path, "x", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metadata in metadata_list:
            row = dict(metadata)
            row["original_shape"] = str(row["original_shape"])
            row["processed_shape"] = str(row["processed_shape"])
            writer.writerow(row)

    logger.info("Metadata written: %s  (%d records)", output_path, len(metadata_list))


def main() -> None:
    """Create a separate clip400 dataset with raw SI; preserve historical artifacts."""
    metadata = prepare_dataset()
    if metadata:
        save_metadata_csv(metadata)
        logger.info("Created %d observations: clip400 B+/B-, raw SI pixel percent", len(metadata))


if __name__ == "__main__":
    main()
