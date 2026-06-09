"""Preprocess HMI FITS files into Coronium V3 PRO tensors.

The model contract is `(2, 512, 512)`: channel 0 is B+ and channel 1 is B-,
both derived from the symmetric log-scaled magnetogram. The sunspot proxy is
computed before resize so interpolation does not change the active-pixel count.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import warnings

import numpy as np
import sunpy.map
from skimage.transform import resize
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


def log_scale(x: np.ndarray) -> np.ndarray:
    """Apply the sign-preserving log transform used by V3 PRO.

    It compresses strong umbral fields without the information loss introduced
    by the older +/-400 G hard clip.

    Args:
        x: Magnetic field array in Gauss (any shape). May contain negative
            values; the sign of each element is preserved.

    Returns:
        An array of the same shape as ``x`` where each element is
        ``sign(x) * log1p(|x|)``.
    """
    return np.sign(x) * np.log1p(np.abs(x))


def load_and_process_magnetogram(
    fits_path: Path,
    target_size: int = 512,
    sunspot_threshold: float = 200.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load, resample, log-scale, and decompose a single HMI FITS magnetogram.

    The sunspot proxy index is computed on the original, pre-resample pixel
    array to avoid double-counting artefacts introduced by bilinear
    interpolation near the 200 G detection threshold.

    Args:
        fits_path: Path to a single HMI line-of-sight FITS file.
        target_size: Edge length, in pixels, of the square output tensor.
            Defaults to 512.
        sunspot_threshold: Strong-field cutoff in Gauss for the sunspot proxy
            index. Defaults to 200.0.

    Returns:
        A 2-tuple ``(tensor, metadata)`` where ``tensor`` is a
        ``(2, target_size, target_size)`` float32 array (channel 0 = B+,
        channel 1 = B-) and ``metadata`` is a dict with keys ``filename``,
        ``date``, ``sunspot_index``, ``original_shape``, ``processed_shape``,
        ``b_pos_max``, ``b_neg_max``, ``mean_b_pos``, and ``mean_b_neg``.

    Raises:
        Exception: Re-raised after logging if SunPy cannot read the FITS file
            or the array cannot be processed.
    """
    try:
        solar_map = sunpy.map.Map(str(fits_path))
        data: np.ndarray = solar_map.data

        data = np.nan_to_num(data, nan=0.0)

        strong_field_mask: np.ndarray = np.abs(data) > sunspot_threshold
        sunspot_index: float = (np.sum(strong_field_mask) / data.size) * 100.0

        data_resampled: np.ndarray = resize(
            data,
            (target_size, target_size),
            mode="reflect",
            anti_aliasing=True,
            preserve_range=True,
        )
        data_resampled = np.nan_to_num(data_resampled, nan=0.0)

        # Symmetric log scaling: x' = sign(x) * log(1 + |x|)
        data_log: np.ndarray = log_scale(data_resampled)

        # Polarity decomposition into two non-negative channels
        b_pos: np.ndarray = np.maximum(data_log, 0.0)   # ReLU(x')
        b_neg: np.ndarray = np.maximum(-data_log, 0.0)  # ReLU(-x')

        # Stack into (2, H, W) tensor — channel 0: B+, channel 1: B-
        processed: np.ndarray = np.stack([b_pos, b_neg], axis=0)

        metadata: Dict[str, Any] = {
            "filename": fits_path.stem,
            "date": solar_map.date.iso,
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
    processed_dir: str = "data/processed",
    target_size: int = 512,
    sunspot_threshold: float = 200.0,
) -> List[Dict[str, Any]]:
    """Batch-process all FITS files in ``raw_dir`` and write dual-channel .npy tensors.

    Files are processed in sorted order for reproducibility. Errors on
    individual files are logged and skipped; processing continues to enable
    partial recovery from corrupt or incomplete JSOC downloads.

    Args:
        raw_dir: Directory containing input ``*.fits`` magnetograms.
            Defaults to ``"data/raw"``.
        processed_dir: Output directory for ``.npy`` tensors; created if it
            does not exist. Defaults to ``"data/processed"``.
        target_size: Edge length, in pixels, of each square output tensor.
            Defaults to 512.
        sunspot_threshold: Strong-field cutoff in Gauss for the sunspot proxy
            index. Defaults to 200.0.

    Returns:
        A list of per-file metadata dicts (see
        :func:`load_and_process_magnetogram`). Empty if ``raw_dir`` contains
        no FITS files.
    """
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    raw_path = Path(raw_dir)
    fits_files: List[Path] = sorted(raw_path.glob("*.fits"))

    if not fits_files:
        logger.warning("No FITS files found in %s", raw_dir)
        return []

    logger.info(
        "%d files to process  |  output: 2 x %dx%d px  |  scaling: log1p",
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
    """Apply Z-Score standardization to ``sunspot_index`` in-place and persist the scaler.

    The raw ``sunspot_index`` value is preserved under the key
    ``sunspot_index_raw`` to allow debugging and distribution checks
    after the fact.
    """
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
    with open(scaler_file, "w") as f:
        json.dump({"mean": mean, "std": std}, f, indent=2)

    logger.info(
        "Target scaler saved: %s  |  mean=%.4f  std=%.4f",
        scaler_file.absolute(), mean, std,
    )
    return mean, std


def save_metadata_csv(
    metadata_list: List[Dict[str, Any]],
    output_path: str = "data/processed/metadata_processed.csv",
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
        "sunspot_index",        # Z-Score normalised value (model input)
        "sunspot_index_raw",    # Original value before normalisation
        "processed_file",
        "original_shape",
        "processed_shape",
        "b_pos_max",
        "b_neg_max",
        "mean_b_pos",
        "mean_b_neg",
    ]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metadata in metadata_list:
            row = dict(metadata)
            row["original_shape"] = str(row["original_shape"])
            row["processed_shape"] = str(row["processed_shape"])
            writer.writerow(row)

    logger.info("Metadata written: %s  (%d records)", output_path, len(metadata_list))


def main() -> None:
    """Execute the V3 PRO dataset preprocessing pipeline."""
    logger.info("=" * 70)
    logger.info("Auralis — Dataset Preparation  [V3 PRO / log1p + dual-channel]")
    logger.info("=" * 70)

    metadata = prepare_dataset(
        raw_dir="data/raw",
        processed_dir="data/processed",
        target_size=512,
        sunspot_threshold=200.0,
    )

    if metadata:
        # ── Z-Score normalization of the regression target ───────────────────
        # Must be applied BEFORE writing the CSV so that the persisted
        # sunspot_index values match what the model will receive at training
        # time. The raw values are kept under sunspot_index_raw for auditing.
        mean, std = normalize_sunspot_targets(
            metadata,
            scaler_path="models/target_scaler.json",
        )

        save_metadata_csv(metadata, output_path="data/processed/metadata_processed.csv")

        raw_indices = [m["sunspot_index_raw"] for m in metadata]
        norm_indices = [m["sunspot_index"] for m in metadata]
        b_pos_maxima = [m["b_pos_max"] for m in metadata]
        b_neg_maxima = [m["b_neg_max"] for m in metadata]
        logger.info("=" * 70)
        logger.info("Dataset statistics:")
        logger.info("  Images:            %d", len(metadata))
        logger.info("  Tensor shape:      (2, 512, 512) — [B+, B-]")
        logger.info("  Sunspot index (raw)  — mean: %.4f  std: %.4f  "
                    "min: %.4f  max: %.4f",
                    np.mean(raw_indices), np.std(raw_indices),
                    np.min(raw_indices), np.max(raw_indices))
        logger.info("  Sunspot index (norm) — mean: %.4f  std: %.4f  "
                    "min: %.4f  max: %.4f  [Z-Score: μ=%.4f σ=%.4f]",
                    np.mean(norm_indices), np.std(norm_indices),
                    np.min(norm_indices), np.max(norm_indices), mean, std)
        logger.info("  B+ max  — mean: %.3f  max: %.3f",
                    np.mean(b_pos_maxima), np.max(b_pos_maxima))
        logger.info("  B- max  — mean: %.3f  max: %.3f",
                    np.mean(b_neg_maxima), np.max(b_neg_maxima))
        logger.info("=" * 70)
    else:
        logger.error("No files processed successfully.")


if __name__ == "__main__":
    main()
