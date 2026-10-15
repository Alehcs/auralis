"""Historical resumable JSOC ETL; predates current dual-channel tensors, so convert outputs before V3 use."""

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
    """Sampling, preprocessing and JSOC throttling; sleeps are empirical (lower values trigger 429/503)."""

    TOTAL_IMAGES: int = 2000

    # Solar Cycles 24-25 (2016-2026); 2019-2020 deep minimum excluded to avoid biasing toward quiet Sun.
    PERIOD_1: Dict = {
        "name": "2016-2018",
        "start": "2016-01-01",
        "end": "2018-12-31",
        "samples": int(TOTAL_IMAGES * 0.3),
    }
    PERIOD_2: Dict = {
        "name": "2021-2023",
        "start": "2021-01-01",
        "end": "2023-12-31",
        "samples": int(TOTAL_IMAGES * 0.3),
    }
    PERIOD_3: Dict = {
        "name": "2024-2026",
        "start": "2024-01-01",
        "end": "2026-12-31",
        "samples": TOTAL_IMAGES - 2 * int(TOTAL_IMAGES * 0.3),
    }

    # Larger batches mean fewer inter-batch pauses without raising the per-IP request rate.
    BATCH_SIZE: int = 100
    TARGET_SIZE: int = 512
    CLIP_VALUE: float = 400.0
    SUNSPOT_THRESHOLD: float = 200.0

    # Inter-request pause (s) keeps < ~25 req/min; below 1.5 s JSOC returns 429 on long runs.
    SLEEP_MIN: float = 1.5
    SLEEP_MAX: float = 3.0

    # Inter-batch pause (s): JSOC connection pools recovered within 20-45 s at BATCH_SIZE=100.
    BATCH_SLEEP_MIN: float = 20.0
    BATCH_SLEEP_MAX: float = 45.0

    MAX_RETRIES: int = 7
    BACKOFF_BASE: int = 2  # Wait 2^n seconds on 429/503 responses.

    RAW_DIR: Path = Path("data/raw")
    PROCESSED_DIR: Path = Path("data/processed")
    METADATA_CSV: Path = PROCESSED_DIR / "metadata_processed.csv"


def generate_sampling_dates(config: Config) -> List[datetime]:
    """Uniformly sample dates per solar-cycle window (avoids fixed-grid artefacts, keeps period quotas)."""
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
    """Fetch the HMI frame nearest ``date`` (1 h window); only 429/503 failures are retried with backoff."""
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
    """Legacy single-channel FITS preprocessing (SI before resampling); convert before V3 use."""
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
    """Check that a saved legacy tensor is complete and in the expected range."""
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
    """Persist metadata immediately so interrupted batches can resume."""
    df = pd.DataFrame([metadata])
    df.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)


def get_processed_files(csv_path: Path) -> Set[str]:
    """Read processed filename stems used as the resume checkpoint."""
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
    """Batched download, transform, validation and raw-FITS cleanup; updates ``processed_files`` in place."""
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
    logger.info("Auralis — Massive Ingest")
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
