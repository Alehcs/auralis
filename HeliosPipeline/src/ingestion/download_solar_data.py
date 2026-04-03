"""Single-date HMI magnetogram downloader via NASA JSOC / SunPy Fido.

Fetches one HMI Level-1.5 LOS magnetogram per target timestamp from the
JSOC ``hmi.m_45s`` data series. Each query uses a ±5-minute window around
the requested time: this guarantees at most one frame is returned at the
45-second cadence without requiring the caller to know the exact TAI
timestamp of the nearest exposure.

The ``a.Sample(24*u.hour)`` attribute coarse-grains the JSOC query to
one result per day, preventing the server from returning the full
1,920-image/day cadence of the 45-second series when the time window
spans multiple hours.

Usage::

    python -m src.ingestion.download_solar_data
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Union

import astropy.units as u
from sunpy.net import Fido, attrs as a


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_solar_data(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    sample_rate: int = 24,
    download_dir: str = "data/raw",
    instrument: str = "hmi",
    physobs: str = "los_magnetic_field",
) -> List[str]:
    """Download one HMI magnetogram per sampling interval between two dates.

    Iterates over timestamps spaced ``sample_rate`` hours apart from
    ``start_date`` to ``end_date``. For each timestamp a JSOC Fido query
    with a ±5-minute window retrieves the nearest available Level-1.5 frame.
    Only the first result is fetched when multiple files satisfy the query
    (duplicates are rare at 24-hour intervals but possible during re-ingestion
    windows after JSOC reprocessing).

    JSOC imposes per-IP rate limits; callers running large date ranges should
    use ``massive_ingest_pipeline`` instead, which adds exponential-backoff
    retry and inter-batch sleep.

    Args:
        start_date: Start of the download window, as ``"YYYY-MM-DD"`` or a
            ``datetime`` object.
        end_date: End of the download window (inclusive).
        sample_rate: Hours between successive target timestamps (default 24).
        download_dir: Local directory for downloaded FITS files (created if
            absent).
        instrument: JSOC instrument identifier (default ``"hmi"``).
        physobs: Physical observable string passed to ``a.Physobs``
            (default ``"los_magnetic_field"``).

    Returns:
        List of absolute path strings for every successfully downloaded file.
        Files that returned no JSOC results or raised exceptions are omitted.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    logger.info(
        "Download window: %s to %s  |  interval: %d h",
        start_date.date(), end_date.date(), sample_rate,
    )

    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", download_path.absolute())

    sample_times: List[datetime] = []
    current = start_date
    while current <= end_date:
        sample_times.append(current)
        current += timedelta(hours=sample_rate)

    logger.info("Target timestamps: %d", len(sample_times))

    downloaded_files: List[str] = []

    for idx, sample_time in enumerate(sample_times, 1):
        try:
            # ±5-minute window: wide enough to catch the nearest 45-second
            # HMI frame without spanning two consecutive cadence intervals.
            time_start = sample_time - timedelta(minutes=5)
            time_end = sample_time + timedelta(minutes=5)

            logger.info("[%d/%d] Querying %s", idx, len(sample_times), sample_time)

            query = Fido.search(
                a.Time(time_start, time_end),
                a.Instrument(instrument),
                a.Physobs(physobs),
                a.Sample(24 * u.hour),
            )

            if len(query) == 0:
                logger.warning("No data available for %s", sample_time)
                continue

            logger.info("  Results: %d  —  fetching first", len(query[0]))

            downloaded = Fido.fetch(
                query[0, 0],
                path=str(download_path / "{file}"),
                progress=True,
            )

            paths = list(downloaded)
            downloaded_files.extend(paths)

            if paths:
                logger.info("  Saved: %s", Path(paths[0]).name)

        except Exception as exc:
            logger.error("Failed for %s: %s", sample_time, exc)

    logger.info("Download complete  |  files: %d", len(downloaded_files))
    return downloaded_files


def main() -> None:
    """Download the past 14 days of daily HMI magnetograms.

    The end date is set two days before the current UTC date because JSOC
    Level-1.5 processing has an approximate 48-hour latency; querying more
    recent dates returns empty result sets.
    """
    end_date = datetime.utcnow() - timedelta(days=2)
    start_date = end_date - timedelta(days=14)

    logger.info("=" * 60)
    logger.info("HeliosPipeline — Solar Data Ingestion")
    logger.info("=" * 60)

    files = fetch_solar_data(
        start_date=start_date,
        end_date=end_date,
        sample_rate=24,
        download_dir="data/raw",
    )

    if files:
        logger.info("=" * 60)
        for f in files:
            logger.info("  %s", Path(f).name)
        logger.info("=" * 60)
    else:
        logger.warning("No files downloaded.")


if __name__ == "__main__":
    main()
