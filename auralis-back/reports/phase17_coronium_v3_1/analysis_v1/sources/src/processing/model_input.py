"""Input contract for the existing Coronium V3 PRO checkpoint (see docs/phase1.md).

Stored single-channel data is clip(resize(B), -400, 400) / 400, NOT Gauss
and NOT log-scaled. Channel 0 is its positive part; channel 1 its negative
magnitude. Already split arrays must use that same dimensionless scale.
"""

import numpy as np

INPUT_CONTRACT = "hmi-clip400-polarity-v1"
TARGET_CONTRACT = "strong-field-pixel-percent-200G-v1"


def processed_filename(row) -> str:
    """Resolve the historical CSV column-swap without changing source rows."""
    value = str(row["processed_file"])
    return f"{row['filename']}_processed.npy" if value.startswith("(") else value


def prepare_model_input(data: np.ndarray) -> np.ndarray:
    """Return contiguous float32 (2, 512, 512), before training augmentation.

    Do not silently reinterpret raw Gauss, log-scaled data, NaNs or other sizes.
    Array values alone cannot prove provenance; callers must supply the stated
    clip400 representation, including for uploaded, already split arrays.
    """
    data = np.asarray(data)
    if data.shape not in ((512, 512), (2, 512, 512)):
        raise ValueError(f"Expected (512, 512) or (2, 512, 512), got {data.shape}")
    if not np.isfinite(data).all() or np.max(np.abs(data)) > 1.0:
        raise ValueError("Expected finite clip400-normalized values in [-1, 1]")
    if data.ndim == 2:
        data = np.stack([np.maximum(data, 0.0), np.maximum(-data, 0.0)])
    elif np.any(data < 0) or np.any((data[0] > 0) & (data[1] > 0)):
        raise ValueError("B+/B- must be nonnegative, mutually exclusive polarities")
    return np.ascontiguousarray(data, dtype=np.float32)


def normalize_field(data: np.ndarray, target_size: int = 512,
                    clip_value: float = 400.0) -> np.ndarray:
    """Reproduce the stored single-channel representation from a FITS B array."""
    from skimage.transform import resize

    data = np.nan_to_num(data, nan=0.0)
    resized = resize(data, (target_size, target_size), mode="reflect",
                     anti_aliasing=True, preserve_range=True)
    resized = np.nan_to_num(resized, nan=0.0)
    return (np.clip(resized, -clip_value, clip_value) / clip_value).astype(np.float32)
