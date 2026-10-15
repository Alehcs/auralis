"""Read-only join of selection-validation predictions to metadata; raises AgentDataError, never writes."""

from __future__ import annotations

import csv
import hashlib
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

# Activity-bin thresholds (raw SI pp), mirroring the /api/predict _classify bands.
BIN_LOW_MAX = 1.41        # low:    SI < 1.41
BIN_MEDIUM_MAX = 1.75     # medium: 1.41 <= SI < 1.75 ; high: SI >= 1.75
TAIL_EXTREME_SI = 2.0     # tail/extreme event marker

ACTIVITY_BINS = ("low", "medium", "high")
EXPECTED_RANDOM_STATE = 42


class AgentDataError(RuntimeError):
    """Missing artifact or broken split contract; ``code`` and ``missing`` feed structured API errors."""

    def __init__(self, message: str, *, code: str, missing: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.missing = missing or []

    def to_dict(self) -> Dict[str, object]:
        return {"error": str(self), "code": self.code, "missing": self.missing}


def activity_bin(sunspot_index: float) -> str:
    """Bin a SI value into low / medium / high using the shared thresholds."""
    if sunspot_index < BIN_LOW_MAX:
        return "low"
    if sunspot_index < BIN_MEDIUM_MAX:
        return "medium"
    return "high"


@dataclass
class ValidationRow:
    """One joined selection-validation sample: prediction joined back to its metadata."""

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
    """Shared read-only inputs: all metadata rows, joined validation rows and raw split indices."""

    metadata_rows: List[Dict[str, object]]
    train_indices: List[int]
    val_indices: List[int]
    validation_rows: List[ValidationRow]
    random_state: Optional[int]
    warnings: List[str] = field(default_factory=list)

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
    """Load and join the read-only agent artifacts; raise AgentDataError rather than use a broken join."""
    from models import serving_selection as serving
    if serving.IS_RELEASE_V32:
        return _load_release_dataset(serving)
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
            f"{EXPECTED_RANDOM_STATE}. The selection-validation join is only valid for the "
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

        # Row-order join check: results truth must equal metadata sunspot_index for the same val index.
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
        # Tolerate a few drifting rows (independently regenerated CSVs); a large fraction means a broken join.
        frac = join_drift / len(validation_rows)
        if frac > 0.05:
            raise AgentDataError(
                f"Join integrity check failed: {join_drift}/{len(validation_rows)} "
                "selection-validation rows do not match metadata ground-truth. The row-order "
                "join between results_comparison.csv and split_indices.json['val'] "
                "appears invalid.",
                code="join_drift",
                missing=[],
            )
        warnings.append(
            f"{join_drift} selection-validation rows drifted slightly from metadata "
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


def _load_release_dataset(serving) -> AgentDataset:
    """Join verified full-precision release predictions by identity, never row guessing."""
    try:
        serving.load_release()
        manifest = json.loads(serving.MANIFEST_PATH.read_text())
        split_path = BASE_DIR / 'models/split_indices_phase1_v1.json'
        for path, key in [(split_path, 'split_sha256'), (METADATA_CSV, 'metadata_sha256')]:
            if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[key]:
                raise ValueError(f'Release dataset hash mismatch: {path.name}')
        split = json.loads(split_path.read_text())
        metadata = _read_metadata(METADATA_CSV)
        with serving.COMPARISON_PATH.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != len(split['val']) or set(split['train']) & set(split['val']):
            raise ValueError('Invalid release split or prediction count')
        joined = []
        for row, index in zip(rows, split['val']):
            meta = metadata[index]
            real, prediction = float(row['target_si']), float(row['kleidiai_off_si'])
            if (int(row['source_row']) != index or row['processed_file'] != meta['processed_file'] or
                    not math.isclose(real, float(meta['sunspot_index']), rel_tol=0, abs_tol=1e-6) or
                    not math.isfinite(prediction)):
                raise ValueError('Release row/filename/target mismatch')
            joined.append(ValidationRow(filename=row['processed_file'], date=(meta.get('date') or '')[:10] or None,
                real=real, predicted=prediction, error=abs(prediction-real), residual=prediction-real,
                activity_bin=activity_bin(real), is_tail_extreme=real > TAIL_EXTREME_SI))
        return AgentDataset(metadata_rows=metadata, train_indices=split['train'], val_indices=split['val'],
            validation_rows=joined, random_state=42, warnings=[
                serving.MODEL_NAME + '; ' + serving.EVALUATION_PROTOCOL,
                'Selection validation, not independent or temporal test. Metadata CSV date scale is unknown.',
                'Low-band deterioration within tolerance and negative R2; border/background XAI concerns remain.',
                'XAI inventory is not a new measurement; saved D/F evidence remains separate.'])
    except (OSError, ValueError, KeyError) as exc:
        raise AgentDataError(str(exc), code='release_evidence_invalid') from exc
