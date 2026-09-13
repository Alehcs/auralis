"""Versioned runtime artifacts for the controlled Coronium V3.1 promotion."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "Coronium V3.1"
MODEL_VERSION = "3.1"
CHECKPOINT_PATH = ROOT / "models/best_coronium_v3_1.pth"
ONNX_PATH = ROOT / "models/best_coronium_v3_1.onnx"
METRICS_PATH = ROOT / "models/coronium_v3_1_metrics.json"
MANIFEST_PATH = ROOT / "models/coronium_v3_1_manifest.json"
COMPARISON_PATH = ROOT / "reports/phase16_coronium_v3_1/coronium_v3_1_mc_results_comparison.csv"
METRICS_STATUS = "clean_observation_validation_used_for_selection_not_independent_test_or_temporal_validation"


def load_release() -> dict:
    """Reject missing or mixed release artifacts before serving V3.1."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    if manifest["model_version"] != MODEL_VERSION:
        raise ValueError("Unexpected active model version")
    for path in (CHECKPOINT_PATH, ONNX_PATH, METRICS_PATH, COMPARISON_PATH):
        expected = manifest["artifacts_sha256"][str(path.relative_to(ROOT))]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Coronium V3.1 artifact hash mismatch: {path.name}")
    return json.loads(METRICS_PATH.read_text())
