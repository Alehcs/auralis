"""Shared read-only dataset loader for the Auralis Agent Lab.

This module is the single source of truth for the join between the promoted
hold-out predictions and the per-sample metadata. It is intentionally the only
place that knows how ``results_comparison.csv`` maps back to
``metadata_processed.csv`` via ``split_indices.json``.

Read-only contract
------------------
Nothing here writes, mutates, or re-derives any artifact. It opens three files
for reading and returns plain Python objects. If a file is missing or the split
contract is violated, it raises :class:`AgentDataError` with a structured,
human-readable detail so the API can degrade gracefully instead of crashing.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# auralis-back/  (src/agents/data_loader.py -> agents -> src -> auralis-back)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
METADATA_CSV = BASE_DIR / "data" / "processed" / "metadata_processed.csv"
SPLIT_JSON = BASE_DIR / "models" / "split_indices.json"
RESULTS_CSV = BASE_DIR / "reports" / "results_comparison.csv"

# Activity-bin thresholds in log-SI space. These mirror the demo-calibrated
# thresholds used by the existing /api/predict classifier (_classify in
# src/api/main.py); they are reused here so the agents bin samples exactly the
# way the rest of the system already does.
BIN_LOW_MAX = 1.41        # low:    SI < 1.41
BIN_MEDIUM_MAX = 1.75     # medium: 1.41 <= SI < 1.75 ; high: SI >= 1.75
TAIL_EXTREME_SI = 2.0     # tail/extreme event marker

ACTIVITY_BINS = ("low", "medium", "high")
EXPECTED_RANDOM_STATE = 42


class AgentDataError(RuntimeError):
    """Raised when a required artifact is missing or the split contract fails.

    Carries a machine-readable ``code`` and the list of ``missing`` paths so the
    API layer can return a clear structured error to the dashboard.
    """

    def __init__(self, message: str, *, code: str, missing: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.missing = missing or []

    def to_dict(self) -> Dict[str, object]:
        return {"error": str(self), "code": self.code, "missing": self.missing}


def activity_bin(sunspot_index: float) -> str:
    """Bin a log-SI value into low / medium / high using the shared thresholds."""
    if sunspot_index < BIN_LOW_MAX:
        return "low"
    if sunspot_index < BIN_MEDIUM_MAX:
        return "medium"
    return "high"


@dataclass
class ValidationRow:
    """One joined hold-out sample: prediction joined back to its metadata."""

    filename: str
    date: Optional[str]
    real: float
    predicted: float
    error: float
    residual: float          # predicted - real (signed)
    activity_bin: str
    is_tail_extreme: bool


@dataclass
class AgentDataset:
    """Everything the read-only agents need, computed once and shared.

    ``metadata_rows`` holds every processed sample; ``validation_rows`` holds the
    joined hold-out predictions. ``train_indices`` / ``val_indices`` are the raw
    split indices into ``metadata_rows``.
    """

    metadata_rows: List[Dict[str, object]]
    train_indices: List[int]
    val_indices: List[int]
    validation_rows: List[ValidationRow]
    random_state: Optional[int]
    warnings: List[str] = field(default_factory=list)

    # -- convenience views --------------------------------------------------

    def metadata_sunspot_indices(self) -> List[float]:
        return [float(r["sunspot_index"]) for r in self.metadata_rows]

    def bin_counts(self, indices: Optional[List[int]] = None) -> Dict[str, int]:
        """Count samples per activity bin, optionally restricted to ``indices``."""
        rows = (
            self.metadata_rows
            if indices is None
            else [self.metadata_rows[i] for i in indices]
        )
        counts = {b: 0 for b in ACTIVITY_BINS}
        for r in rows:
            counts[activity_bin(float(r["sunspot_index"]))] += 1
        return counts


def _require(path: Path, code: str) -> None:
    if not path.exists():
        raise AgentDataError(
            f"Required artifact not found: {path.name} (expected at {path}). "
            "The Agent Lab is read-only and cannot regenerate it.",
            code=code,
            missing=[str(path)],
        )


def _read_metadata(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(dict(row))
    if not rows:
        raise AgentDataError(
            f"{path.name} is empty.", code="empty_metadata", missing=[]
        )
    return rows


def _read_results(path: Path) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "real": float(row["Real_SSN"]),
                    "predicted": float(row["Predicted_SSN"]),
                    "error": float(row["Error_Absoluto"]),
                }
            )
    if not rows:
        raise AgentDataError(
            f"{path.name} is empty.", code="empty_results", missing=[]
        )
    return rows


def load_agent_dataset() -> AgentDataset:
    """Load and join the read-only artifacts the agents depend on.

    Raises :class:`AgentDataError` (with structured detail) when a file is
    missing or the split contract is violated, so callers never silently work
    with a broken join.
    """
    _require(METADATA_CSV, code="missing_metadata")
    _require(SPLIT_JSON, code="missing_split")
    _require(RESULTS_CSV, code="missing_results")

    metadata_rows = _read_metadata(METADATA_CSV)

    with open(SPLIT_JSON, encoding="utf-8") as fh:
        split = json.load(fh)

    val_indices = split.get("val")
    train_indices = split.get("train", [])
    if not isinstance(val_indices, list) or not val_indices:
        raise AgentDataError(
            "split_indices.json has no usable 'val' list.",
            code="bad_split",
            missing=[],
        )

    random_state = split.get("random_state")
    if random_state is not None and random_state != EXPECTED_RANDOM_STATE:
        # The verified row-order join only holds for the promoted seed-42 split.
        raise AgentDataError(
            f"split_indices.json random_state={random_state}, expected "
            f"{EXPECTED_RANDOM_STATE}. The hold-out join is only valid for the "
            "promoted seed-42 split; refusing to produce a misaligned audit.",
            code="unexpected_random_state",
            missing=[],
        )

    results = _read_results(RESULTS_CSV)

    if len(val_indices) != len(results):
        raise AgentDataError(
            f"Split/results length mismatch: len(val)={len(val_indices)} but "
            f"results_comparison.csv has {len(results)} rows. The row-order join "
            "is no longer valid.",
            code="length_mismatch",
            missing=[],
        )

    warnings: List[str] = []
    validation_rows: List[ValidationRow] = []
    n_meta = len(metadata_rows)
    join_drift = 0

    for i, idx in enumerate(val_indices):
        if not isinstance(idx, int) or idx < 0 or idx >= n_meta:
            raise AgentDataError(
                f"val index {idx} out of range for metadata of length {n_meta}.",
                code="index_out_of_range",
                missing=[],
            )
        meta = metadata_rows[idx]
        meta_si = float(meta["sunspot_index"])
        real = results[i]["real"]
        predicted = results[i]["predicted"]
        error = results[i]["error"]

        # Sanity check the join: the ground-truth in results_comparison.csv must
        # match the metadata sunspot_index for the same val index. A drift here
        # would mean the row-order contract has broken.
        if not math.isclose(meta_si, real, abs_tol=1e-2):
            join_drift += 1

        date_raw = str(meta.get("date") or "").strip() or None
        date = date_raw[:10] if date_raw else None

        validation_rows.append(
            ValidationRow(
                filename=str(meta.get("filename") or f"index_{idx}"),
                date=date,
                real=real,
                predicted=predicted,
                error=error,
                residual=round(predicted - real, 6),
                activity_bin=activity_bin(real),
                is_tail_extreme=real > TAIL_EXTREME_SI,
            )
        )

    if join_drift > 0:
        # Tolerate but surface: a few drifting rows hint the CSVs were
        # regenerated independently. A large fraction means the join is broken.
        frac = join_drift / len(validation_rows)
        if frac > 0.05:
            raise AgentDataError(
                f"Join integrity check failed: {join_drift}/{len(validation_rows)} "
                "hold-out rows do not match metadata ground-truth. The row-order "
                "join between results_comparison.csv and split_indices.json['val'] "
                "appears invalid.",
                code="join_drift",
                missing=[],
            )
        warnings.append(
            f"{join_drift} hold-out rows drifted slightly from metadata "
            "ground-truth (within tolerance)."
        )

    return AgentDataset(
        metadata_rows=metadata_rows,
        train_indices=[int(i) for i in train_indices],
        val_indices=[int(i) for i in val_indices],
        validation_rows=validation_rows,
        random_state=random_state,
        warnings=warnings,
    )
