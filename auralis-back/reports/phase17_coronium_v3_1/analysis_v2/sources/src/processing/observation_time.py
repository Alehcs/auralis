"""Keep the filename record time separate from undocumented CSV observation time."""

import re
from functools import lru_cache

_PATTERN = re.compile(
    r"hmi\.m_45s\.(\d{4})\.(\d{2})\.(\d{2})_(\d{2})_(\d{2})_(\d{2})_TAI"
)


@lru_cache(maxsize=4096)
def filename_time(filename: str) -> dict:
    match = _PATTERN.search(filename)
    if not match:
        return {"date": None, "date_original": None, "date_scale": None,
                "date_source": "unrecognized_filename", "date_utc": None}
    y, mo, d, h, mi, s = match.groups()
    original = f"{y}-{mo}-{d}T{h}:{mi}:{s}"
    # Astropy is already in the full environment. Lean API installs can still
    # expose the original TAI time, without pretending it is UTC.
    try:
        from astropy.time import Time
        from astropy.utils import iers
    except ImportError:
        utc = None
    else:
        try:
            with iers.conf.set_temp("auto_download", False):
                utc = Time(original, format="isot", scale="tai").utc.isot + "Z"
        except ValueError:
            return {"date": None, "date_original": original, "date_scale": "TAI",
                    "date_source": "invalid_filename_record_time", "date_utc": None}
    return {"date": utc, "date_original": original, "date_scale": "TAI",
            "date_source": "filename_record_time", "date_utc": utc}
