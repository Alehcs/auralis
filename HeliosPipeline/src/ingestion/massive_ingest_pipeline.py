"""Batch ETL pipeline for large-scale HMI magnetogram acquisition.

Downloads, processes, validates, and persists up to 2,000 HMI Level-1.5
magnetograms from NASA JSOC into the ``data/processed/`` directory. The
pipeline is designed to be interrupted and resumed: processed filenames are
tracked in ``metadata_processed.csv`` and checked before each download to
prevent duplicate fetches.

Temporal distribution:
    - 2011-2013 (25 %): Solar Cycle 24 ascending phase and maximum
      (activity peak ~2013-11), providing high-flux training samples.
    - 2015-2018 (25 %): Cycle 24 declining phase, intermediate activity.
    - 2021-2025 (50 %): Cycle 25 ascending phase (peak expected ~2025),
      oversampled to extend temporal coverage and ensure generalisation to
      current-cycle magnetogram morphology.

Rate-limiting strategy:
    JSOC imposes per-IP rate limits that trigger HTTP 429 after
    approximately 20 requests/minute. A random 2–5 second inter-request
    pause keeps throughput below ~15 requests/minute with jitter to avoid
    periodic patterns. A 30–60 second inter-batch pause allows JSOC
    connection pools to recover between bursts.
"""

import csv
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import sunpy.map
from skimage.transform import resize
from sunpy.net import Fido, attrs as a
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("massive_ingest.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Config:
    """Centralised pipeline parameters.

    Consolidates all tuneable constants to avoid magic numbers scattered
    across the pipeline functions. Update ``TOTAL_IMAGES`` and period
    boundaries here when re-running for a new solar cycle.

    Rate-limit parameters (SLEEP_*, BATCH_SLEEP_*):
        Derived empirically from JSOC connection logs. Values below
        ``SLEEP_MIN=2.0`` seconds consistently trigger 429 responses during
        sustained ingestion runs of > 500 images.

    Retry parameters (MAX_RETRIES, BACKOFF_BASE):
        Exponential backoff ``2^n + U(0,1)`` seconds is consistent with
        RFC 6585 recommendations for HTTP 429 retry-after handling.
    """

    TOTAL_IMAGES: int = 2000

    # Periods sampled proportionally across Solar Cycles 24 and 25.
    # 2014 is excluded: elevated JSOC reprocessing errors during that year.
    PERIOD_1: Dict = {
        "name": "2011-2013",
        "start": "2011-01-01",
        "end": "2013-12-31",
        "samples": int(TOTAL_IMAGES * 0.25),
    }
    PERIOD_2: Dict = {
        "name": "2015-2018",
        "start": "2015-01-01",
        "end": "2018-12-31",
        "samples": int(TOTAL_IMAGES * 0.25),
    }
    PERIOD_3: Dict = {
        "name": "2021-2025",
        "start": "2021-01-01",
        "end": "2025-12-31",
        "samples": TOTAL_IMAGES - 2 * int(TOTAL_IMAGES * 0.25),
    }

    BATCH_SIZE: int = 50
    TARGET_SIZE: int = 512
    CLIP_VALUE: float = 400.0
    SUNSPOT_THRESHOLD: float = 200.0

    # Inter-request pause (seconds): keeps request rate < 15/minute.
    SLEEP_MIN: float = 2.0
    SLEEP_MAX: float = 5.0

    # Inter-batch pause (seconds): allows JSOC connection pool recovery.
    BATCH_SLEEP_MIN: float = 30.0
    BATCH_SLEEP_MAX: float = 60.0

    MAX_RETRIES: int = 5
    BACKOFF_BASE: int = 2  # Wait 2^n seconds on 429/503 responses.

    RAW_DIR: Path = Path("data/raw")
    PROCESSED_DIR: Path = Path("data/processed")
    METADATA_CSV: Path = PROCESSED_DIR / "metadata_processed.csv"


def generate_sampling_dates(config: Config) -> List[datetime]:
    """Draw random dates uniformly from each configured solar-cycle period.

    Uniform random sampling within each period prevents systematic
    temporal bias (e.g., preferential sampling of solar minima) that
    would arise from fixed-interval grids. Dates are drawn independently
    per period and sorted chronologically before return.

    Args:
        config: Pipeline configuration instance containing period boundaries
            and per-period sample counts.

    Returns:
        Sorted list of ``datetime`` objects with length ``config.TOTAL_IMAGES``.
    """
    logger.info("Generating sampling dates for %d images...", config.TOTAL_IMAGES)

    all_dates: List[datetime] = []

    for period in (config.PERIOD_1, config.PERIOD_2, config.PERIOD_3):
        start = datetime.strptime(period["start"], "%Y-%m-%d")
        end = datetime.strptime(period["end"], "%Y-%m-%d")
        span_days = (end - start).days
        for _ in range(period["samples"]):
            all_dates.append(start + timedelta(days=random.randint(0, span_days)))

    all_dates.sort()

    logger.info(
        "Dates generated — %s: %d  |  %s: %d  |  %s: %d",
        config.PERIOD_1["name"], config.PERIOD_1["samples"],
        config.PERIOD_2["name"], config.PERIOD_2["samples"],
        config.PERIOD_3["name"], config.PERIOD_3["samples"],
    )

    return all_dates


def download_with_retry(
    date: datetime,
    download_dir: Path,
    config: Config,
) -> Optional[Path]:
    """Fetch the HMI magnetogram nearest to ``date`` with exponential-backoff retry.

    Issues a JSOC Fido query over a 1-hour window starting at ``date``
    (wider than the ±5-minute window used in the single-shot downloader to
    account for occasional data gaps in the 45-second series). On HTTP 429
    or 503 responses, waits ``2^attempt + U(0,1)`` seconds before retrying.
    Non-rate-limit errors are treated as permanent failures and return ``None``
    immediately to avoid stalling the batch on corrupt JSOC records.

    Args:
        date: Target observation date.
        download_dir: Destination directory for the downloaded FITS file.
        config: Pipeline configuration supplying retry and sleep parameters.

    Returns:
        ``Path`` to the downloaded FITS file, or ``None`` on failure.
    """
    for attempt in range(config.MAX_RETRIES):
        try:
            time_range = a.Time(date, date + timedelta(hours=1))
            query = Fido.search(
                time_range,
                a.Instrument("HMI"),
                a.Physobs("LOS_magnetic_field"),
            )

            if len(query) == 0:
                logger.warning("No data for %s", date.strftime("%Y-%m-%d"))
                return None

            downloaded = Fido.fetch(
                query[0, 0],
                path=str(download_dir / "{file}"),
                progress=False,
            )

            file_path = Path(list(downloaded)[0])
            time.sleep(random.uniform(config.SLEEP_MIN, config.SLEEP_MAX))
            return file_path

        except Exception as exc:
            if "429" in str(exc) or "503" in str(exc):
                wait = config.BACKOFF_BASE ** attempt + random.uniform(0, 1)
                logger.warning(
                    "Rate limit (attempt %d/%d) — waiting %.1f s",
                    attempt + 1, config.MAX_RETRIES, wait,
                )
                time.sleep(wait)
            else:
                logger.error("Download failed for %s: %s", date, exc)
                return None

    logger.error("Max retries exceeded for %s", date)
    return None


def process_magnetogram(
    fits_path: Path,
    config: Config,
) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
    """Load and normalise a single HMI FITS file into a float32 tensor.

    Replicates the normalisation chain defined in ``prepare_dataset`` to
    ensure consistency between the batch ingestion pipeline and the
    standalone preprocessing module. The sunspot proxy index is computed
    before resampling to avoid interpolation artefacts near the 200 G
    detection threshold (see ``prepare_dataset`` module docstring).

    Args:
        fits_path: Path to the downloaded HMI Level-1.5 FITS file.
        config: Pipeline configuration supplying ``TARGET_SIZE``,
            ``CLIP_VALUE``, and ``SUNSPOT_THRESHOLD``.

    Returns:
        Tuple of:
            - float32 ndarray of shape ``(512, 512)`` normalised to ``[-1, 1]``,
              or ``None`` on error.
            - Metadata dictionary, or ``None`` on error.
    """
    try:
        solar_map = sunpy.map.Map(str(fits_path))
        data = solar_map.data
        data = np.nan_to_num(data, nan=0.0)

        strong_field = np.abs(data) > config.SUNSPOT_THRESHOLD
        sunspot_index = (np.sum(strong_field) / data.size) * 100.0

        data_resampled = resize(
            data,
            (config.TARGET_SIZE, config.TARGET_SIZE),
            mode="reflect",
            anti_aliasing=True,
            preserve_range=True,
        )
        data_resampled = np.nan_to_num(data_resampled, nan=0.0)

        data_normalized = (
            np.clip(data_resampled, -config.CLIP_VALUE, config.CLIP_VALUE)
            / config.CLIP_VALUE
        )

        metadata: Dict = {
            "filename": fits_path.stem,
            "date": solar_map.date.iso,
            "sunspot_index": sunspot_index,
            "original_shape": str(data.shape),
            "processed_shape": str(data_normalized.shape),
            "min_value": float(np.min(data_normalized)),
            "max_value": float(np.max(data_normalized)),
            "mean_value": float(np.mean(data_normalized)),
        }

        return data_normalized.astype(np.float32), metadata

    except Exception as exc:
        logger.error("Processing failed for %s: %s", fits_path.name, exc)
        return None, None


def validate_npy_file(npy_path: Path) -> bool:
    """Verify that a serialised tensor is structurally sound.

    Checks three necessary conditions for a valid processed magnetogram:
    (1) file size > 100 bytes (rules out empty or truncated writes),
    (2) array shape equals ``(512, 512)`` (matches training pipeline output),
    (3) all values lie within ``[-1.1, 1.1]`` (10 % tolerance over the
    nominal ``[-1, 1]`` range to absorb floating-point rounding after
    the clip-and-scale operation).

    Args:
        npy_path: Path to the ``.npy`` file to validate.

    Returns:
        ``True`` if all three conditions pass, ``False`` otherwise.
    """
    try:
        if not npy_path.exists():
            return False
        if npy_path.stat().st_size < 100:
            logger.error("File appears empty or truncated: %s", npy_path.name)
            return False
        data = np.load(str(npy_path))
        if data.shape != (512, 512):
            logger.error("Unexpected shape %s in %s", data.shape, npy_path.name)
            return False
        if np.min(data) < -1.1 or np.max(data) > 1.1:
            logger.error(
                "Values out of range [%.3f, %.3f] in %s",
                np.min(data), np.max(data), npy_path.name,
            )
            return False
        return True
    except Exception as exc:
        logger.error("Validation error for %s: %s", npy_path.name, exc)
        return False


def append_to_csv(metadata: Dict, csv_path: Path) -> None:
    """Append one metadata row to the CSV, writing the header on first call.

    Uses pandas ``DataFrame.to_csv`` in append mode so each successful
    magnetogram is persisted immediately. This ensures partial progress is
    recoverable if the pipeline is interrupted mid-batch.

    Args:
        metadata: Dictionary with the column set produced by
            ``process_magnetogram``.
        csv_path: Destination CSV path (created if absent).
    """
    df = pd.DataFrame([metadata])
    df.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)


def get_processed_files(csv_path: Path) -> Set[str]:
    """Return the set of already-processed filenames from the metadata CSV.

    Enables resume-from-checkpoint behaviour: the pipeline checks this set
    before downloading each file and skips dates whose stem already appears
    in the CSV.

    Args:
        csv_path: Path to the metadata CSV written by ``append_to_csv``.

    Returns:
        Set of filename stems (without extension) that have been processed,
        or an empty set if the CSV does not exist or lacks a ``filename``
        column.
    """
    if not csv_path.exists():
        return set()
    try:
        df = pd.read_csv(csv_path)
        if "filename" in df.columns:
            return set(df["filename"].values)
        logger.warning("CSV has no 'filename' column — returning empty set")
        return set()
    except Exception as exc:
        logger.error("Could not read CSV: %s", exc)
        return set()


def process_batch_etl(
    dates: List[datetime],
    config: Config,
    processed_files: Set[str],
) -> Dict[str, int]:
    """Execute the full Extract-Transform-Load pipeline in batches.

    Each batch of ``config.BATCH_SIZE`` dates passes through three sequential
    phases:
        1. Download — JSOC Fido fetch with exponential-backoff retry.
        2. Transform + Validate — normalise to float32, validate shape and range.
        3. Cleanup — delete raw FITS files to reclaim disk space after
           successful processing. Raw files are removed regardless of
           processing outcome to prevent indefinite disk growth.

    Args:
        dates: Full list of target observation dates to process.
        config: Pipeline configuration.
        processed_files: Mutable set of already-processed filename stems,
            updated in-place as files are successfully persisted.

    Returns:
        Dictionary with integer counters for keys:
        ``total``, ``already_processed``, ``downloaded``, ``processed``,
        ``failed_download``, ``failed_processing``, ``failed_validation``.
    """
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    stats: Dict[str, int] = {
        "total": len(dates),
        "already_processed": 0,
        "downloaded": 0,
        "processed": 0,
        "failed_download": 0,
        "failed_processing": 0,
        "failed_validation": 0,
    }

    total_batches = (len(dates) + config.BATCH_SIZE - 1) // config.BATCH_SIZE

    logger.info("=" * 70)
    logger.info(
        "Massive ingestion  |  images: %d  |  batches: %d (size: %d)",
        len(dates), total_batches, config.BATCH_SIZE,
    )
    logger.info("=" * 70)

    for batch_idx in range(total_batches):
        batch_start = batch_idx * config.BATCH_SIZE
        batch_dates = dates[batch_start: batch_start + config.BATCH_SIZE]

        logger.info(
            "Batch %d/%d  (%d images)",
            batch_idx + 1, total_batches, len(batch_dates),
        )

        batch_files: List[Path] = []

        # Phase 1: Download
        logger.info("  Phase 1: Download")
        for date in tqdm(batch_dates, desc=f"Batch {batch_idx + 1} — Download", leave=False):
            date_str = date.strftime("%Y.%m.%d")

            # Skip dates whose formatted string appears in a processed filename.
            if any(date_str in pf for pf in processed_files):
                stats["already_processed"] += 1
                continue

            fits_path = download_with_retry(date, config.RAW_DIR, config)

            if fits_path is None:
                stats["failed_download"] += 1
                continue

            if fits_path.stem in processed_files:
                fits_path.unlink(missing_ok=True)
                stats["already_processed"] += 1
                continue

            batch_files.append(fits_path)
            stats["downloaded"] += 1

        # Phase 2: Transform and validate
        logger.info("  Phase 2: Transform + Validate (%d files)", len(batch_files))
        for fits_path in tqdm(batch_files, desc=f"Batch {batch_idx + 1} — Process", leave=False):
            processed_data, metadata = process_magnetogram(fits_path, config)

            if processed_data is None:
                stats["failed_processing"] += 1
                continue

            output_filename = f"{fits_path.stem}_processed.npy"
            npy_path = config.PROCESSED_DIR / output_filename
            np.save(str(npy_path), processed_data)

            if not validate_npy_file(npy_path):
                stats["failed_validation"] += 1
                npy_path.unlink(missing_ok=True)
                continue

            metadata["processed_file"] = output_filename
            append_to_csv(metadata, config.METADATA_CSV)
            processed_files.add(metadata["filename"])
            stats["processed"] += 1

        # Phase 3: Cleanup — remove raw FITS to reclaim disk space
        logger.info("  Phase 3: Cleanup")
        for fits_path in batch_files:
            try:
                fits_path.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Could not remove %s: %s", fits_path.name, exc)

        if batch_idx < total_batches - 1:
            sleep_time = random.uniform(config.BATCH_SLEEP_MIN, config.BATCH_SLEEP_MAX)
            logger.info("  Inter-batch pause: %.1f s", sleep_time)
            time.sleep(sleep_time)

    return stats


def main() -> None:
    """Entry point for the massive ingestion pipeline."""
    config = Config()

    logger.info("=" * 70)
    logger.info("HeliosPipeline — Massive Ingest")
    logger.info("=" * 70)

    dates = generate_sampling_dates(config)
    processed_files = get_processed_files(config.METADATA_CSV)

    logger.info(
        "Already processed: %d  |  Pending: %d",
        len(processed_files), len(dates) - len(processed_files),
    )

    t_start = time.time()
    stats = process_batch_etl(dates, config, processed_files)
    elapsed = time.time() - t_start

    logger.info("=" * 70)
    logger.info("Execution summary")
    logger.info("  Total targets:        %d", stats["total"])
    logger.info("  Already processed:    %d", stats["already_processed"])
    logger.info("  Downloaded:           %d", stats["downloaded"])
    logger.info("  Processed:            %d", stats["processed"])
    logger.info("  Failed (download):    %d", stats["failed_download"])
    logger.info("  Failed (processing):  %d", stats["failed_processing"])
    logger.info("  Failed (validation):  %d", stats["failed_validation"])
    logger.info("  Elapsed:              %.2f min", elapsed / 60)
    logger.info("=" * 70)

    if stats["total"] > 0:
        success_rate = stats["processed"] / stats["total"] * 100
        logger.info("Success rate: %.2f%%", success_rate)

    if stats["processed"] > 0:
        logger.info("Output: %s", config.PROCESSED_DIR)
        logger.info("Metadata: %s", config.METADATA_CSV)


if __name__ == "__main__":
    main()
