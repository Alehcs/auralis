"""Local release registry. Explicit staging never changes the persistent default."""

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VERSION = "3.2"  # C1_s42 epoch27; local promotion explicitly authorized in Phase H.
METRICS_STATUS = "clean_observation_validation_used_for_selection_not_independent_test_or_temporal_validation"


def paths(version):
    if version not in ('3.1', '3.2'):
        raise ValueError('AURALIS_RELEASE must be 3.1 or 3.2; no fallback')
    suffix = version.replace('.', '_')
    return dict(checkpoint=ROOT / f'models/best_coronium_v{suffix}.pth',
                onnx=ROOT / f'models/best_coronium_v{suffix}.onnx',
                metrics=ROOT / f'models/coronium_v{suffix}_metrics.json',
                manifest=ROOT / f'models/coronium_v{suffix}_manifest.json',
                comparison=(ROOT / 'reports/phase16_coronium_v3_1/coronium_v3_1_mc_results_comparison.csv'
                            if version == '3.1' else ROOT / 'models/coronium_v3_2_validation.csv'))


MODEL_VERSION = os.environ.get('AURALIS_RELEASE', DEFAULT_VERSION)
MODEL_NAME = f'Coronium V{MODEL_VERSION}'
_paths = paths(MODEL_VERSION)
CHECKPOINT_PATH, ONNX_PATH, METRICS_PATH, MANIFEST_PATH, COMPARISON_PATH = (
    _paths[k] for k in ('checkpoint', 'onnx', 'metrics', 'manifest', 'comparison'))


def _verified_release(version, selected):
    manifest = json.loads(selected['manifest'].read_text())
    if manifest['model_version'] != version:
        raise ValueError('Unexpected release model version')
    for key in ('checkpoint', 'onnx', 'metrics', 'comparison'):
        path = selected[key]
        expected = manifest["artifacts_sha256"][str(path.relative_to(ROOT))]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Coronium V{version} artifact hash mismatch: {path.name}")
    if version == '3.2':
        if not (manifest['seed'] == 42 and manifest['best_epoch'] == 27 and
                manifest['dropout_backbone'] == 0 and manifest['dropout_head'] == .3 and
                manifest['parameters'] == 206875 and manifest['input_shape'] == ['N', 2, 512, 512] and
                manifest['input_contract'] == 'hmi-clip400-polarity-v1' and
                manifest['target_contract'] == 'strong-field-pixel-percent-200G-v1' and
                manifest['runtime']['session_config'] == {'mlas.disable_kleidiai': '1'}):
            raise ValueError('Release configuration does not match the approved C1 checkpoint')
    return json.loads(selected['metrics'].read_text())


def load_version(version):
    """Explicit rollback/control artifacts, independent of the current default."""
    return _verified_release(version, paths(version))


def load_release() -> dict:
    return _verified_release(MODEL_VERSION, dict(checkpoint=CHECKPOINT_PATH, onnx=ONNX_PATH,
        metrics=METRICS_PATH, manifest=MANIFEST_PATH, comparison=COMPARISON_PATH))
