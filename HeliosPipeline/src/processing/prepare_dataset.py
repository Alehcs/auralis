"""Preprocessing pipeline: HMI FITS -> normalised NumPy tensors.

Transforms raw HMI Level-1.5 FITS files downloaded from NASA JSOC into
float32 NumPy arrays suitable for training SolarNet. The normalisation
protocol is fixed at dataset creation time and must be reproduced exactly
at inference (see ``predict.preprocess_fits_image``).

Processing steps applied to each magnetogram:
    1. Load with SunPy to inherit the FITS header coordinate metadata.
    2. Replace NaN values (off-disk limb mask applied by JSOC) with 0.
    3. Compute the sunspot proxy index on the raw, pre-resample array to
       avoid interpolation artefacts inflating the active-pixel count near
       the detection threshold.
    4. Resample to 512 x 512 with bilinear anti-aliasing to standardise
       spatial resolution across the SDO observing baseline (2011-2025),
       during which the SDO-Sun distance varies by approximately +-3%.
    5. Clip to +-400 G and scale linearly to [-1, 1].
    6. Serialise as float32 .npy.
    7. Append a metadata row to the companion CSV.
"""

import csv
import logging
from datetime import datetime
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


def load_and_process_magnetogram(
    fits_path: Path,
    target_size: int = 512,
    clip_value: float = 400.0,
    sunspot_threshold: float = 200.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load, resample, and normalise a single HMI FITS magnetogram.

    The sunspot proxy index is computed on the original, pre-resample pixel
    array to avoid double-counting artefacts introduced by bilinear
    interpolation near the 200 G detection threshold.

    The clip bound of +-400 G follows Bobra & Couvidat (2015): it covers the
    99th percentile of LOS flux density in active regions while preventing
    the <<1% of umbral-core pixels from compressing the dynamic range of the
    normalised array. The 200 G threshold for active-pixel classification is
    consistent with HMI SHARP active-region boundary criteria.

    Args:
        fits_path: Path to an HMI Level-1.5 FITS file.
        target_size: Square output side length in pixels (default 512).
        clip_value: Symmetric saturation bound in Gauss (default 400.0).
        sunspot_threshold: Field strength threshold in Gauss used to classify
            pixels as magnetically active (default 200.0).

    Returns:
        Tuple of:
            - float32 ndarray of shape (target_size, target_size) in [-1, 1].
            - Metadata dictionary with keys: filename, date, sunspot_index,
              original_shape, processed_shape, min_value, max_value,
              mean_value.

    Raises:
        Exception: Propagated from SunPy or skimage on malformed FITS input.
    """
    try:
        solar_map = sunpy.map.Map(str(fits_path))
        data = solar_map.data

        data = np.nan_to_num(data, nan=0.0)

        strong_field_mask = np.abs(data) > sunspot_threshold
        sunspot_index = (np.sum(strong_field_mask) / data.size) * 100.0

        data_resampled = resize(
            data,
            (target_size, target_size),
            mode="reflect",
            anti_aliasing=True,
            preserve_range=True,
        )
        data_resampled = np.nan_to_num(data_resampled, nan=0.0)

        data_normalized = np.clip(data_resampled, -clip_value, clip_value) / clip_value

        metadata: Dict[str, Any] = {
            "filename": fits_path.stem,
            "date": solar_map.date.iso,
            "sunspot_index": sunspot_index,
            "original_shape": data.shape,
            "processed_shape": data_normalized.shape,
            "min_value": float(np.min(data_normalized)),
            "max_value": float(np.max(data_normalized)),
            "mean_value": float(np.mean(data_normalized)),
        }

        return data_normalized.astype(np.float32), metadata

    except Exception as e:
        logger.error("Failed to process %s: %s", fits_path.name, e)
        raise


def prepare_dataset(
    raw_dir: str = "data/raw",
    processed_dir: str = "data/processed",
    target_size: int = 512,
    clip_value: float = 400.0,
    sunspot_threshold: float = 200.0,
) -> List[Dict[str, Any]]:
    """Batch-process all FITS files in ``raw_dir`` and write .npy tensors.

    Files are processed in sorted order for reproducibility. Errors on
    individual files are logged and skipped; processing continues to enable
    partial recovery from corrupt or incomplete JSOC downloads.

    Args:
        raw_dir: Directory containing raw ``.fits`` files.
        processed_dir: Output directory for ``.npy`` tensors (created if
            absent).
        target_size: Square output resolution passed to
            ``load_and_process_magnetogram``.
        clip_value: Clip bound in Gauss.
        sunspot_threshold: Active-region detection threshold in Gauss.

    Returns:
        List of metadata dictionaries, one per successfully processed file.
    """
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    raw_path = Path(raw_dir)
    fits_files = sorted(raw_path.glob("*.fits"))

    if not fits_files:
        logger.warning("No FITS files found in %s", raw_dir)
        return []

    logger.info(
        "%d files to process  |  output: %dx%d px  |  clip: +/-%.0f G",
        len(fits_files), target_size, target_size, clip_value,
    )

    all_metadata: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for fits_file in tqdm(fits_files, desc="Processing magnetograms", unit="file"):
        try:
            processed_data, metadata = load_and_process_magnetogram(
                fits_file,
                target_size=target_size,
                clip_value=clip_value,
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


def save_metadata_csv(
    metadata_list: List[Dict[str, Any]],
    output_path: str = "data/processed/metadata_processed.csv",
) -> None:
    """Write the metadata list to a CSV file.

    Shape tuples are serialised as strings because CSV does not support
    compound types; downstream code should parse them with ``ast.literal_eval``
    if shape comparison is required.

    Args:
        metadata_list: List of dictionaries returned by ``prepare_dataset``.
        output_path: Destination path for the CSV file (parent created if
            absent).
    """
    if not metadata_list:
        logger.warning("No metadata to write.")
        return

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "filename",
        "date",
        "sunspot_index",
        "processed_file",
        "original_shape",
        "processed_shape",
        "min_value",
        "max_value",
        "mean_value",
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
    """Execute the dataset preprocessing pipeline."""
    logger.info("=" * 70)
    logger.info("HeliosPipeline — Dataset Preparation")
    logger.info("=" * 70)

    metadata = prepare_dataset(
        raw_dir="data/raw",
        processed_dir="data/processed",
        target_size=512,
        clip_value=400.0,
        sunspot_threshold=200.0,
    )

    if metadata:
        save_metadata_csv(metadata, output_path="data/processed/metadata_processed.csv")

        indices = [m["sunspot_index"] for m in metadata]
        logger.info("=" * 70)
        logger.info("Dataset statistics:")
        logger.info("  Images:          %d", len(metadata))
        logger.info("  Sunspot index — mean: %.3f  min: %.3f  max: %.3f",
                    np.mean(indices), np.min(indices), np.max(indices))
        logger.info("  Resolution:      512 x 512 px")
        logger.info("  Value range:     [-1.0, 1.0]")
        logger.info("=" * 70)
    else:
        logger.error("No files processed successfully.")


if __name__ == "__main__":
    main()
