"""Per-process selection: AURALIS_RELEASE picks a release, AURALIS_TEST_* the experimental catalog."""
import hashlib
import json
import os
from pathlib import Path
from models import active_model as active

ROOT = active.ROOT
TEST_MODEL = os.environ.get('AURALIS_TEST_MODEL')
TEST_RUNTIME = os.environ.get('AURALIS_TEST_RUNTIME', 'default')
TEST_MODE = TEST_MODEL is not None
if TEST_MODE and 'AURALIS_RELEASE' in os.environ:
    raise ValueError('Do not combine AURALIS_RELEASE with AURALIS_TEST_MODEL')
if TEST_MODEL not in (None, 'V3.1', 'C1_s42', 'C1_s137', 'C1_s2026'):
    raise ValueError('Invalid AURALIS_TEST_MODEL; choose V3.1, C1_s42, C1_s137 or C1_s2026')
if TEST_RUNTIME not in ('default', 'kleidiai_off') or ('AURALIS_TEST_RUNTIME' in os.environ and not TEST_MODE):
    raise ValueError('AURALIS_TEST_RUNTIME requires explicit AURALIS_TEST_MODEL and default or kleidiai_off')
IS_CANDIDATE = TEST_MODE and TEST_MODEL != 'V3.1'
MODEL_NAME, MODEL_VERSION = active.MODEL_NAME, active.MODEL_VERSION
CHECKPOINT_PATH, ONNX_PATH = active.CHECKPOINT_PATH, active.ONNX_PATH
MANIFEST_PATH, COMPARISON_PATH = active.MANIFEST_PATH, active.COMPARISON_PATH
METRICS_STATUS = active.METRICS_STATUS
MODEL_STATUS = 'promoted_clean_phase15_checkpoint'
EVALUATION_PROTOCOL = 'MC Dropout T=20, seed=42, batch=32, MPS; not the deterministic API protocol'
BACKBONE_DROPOUT = 0.2
SEED = 42
IS_RELEASE_V32 = not TEST_MODE and MODEL_VERSION == '3.2'
if TEST_MODEL == 'V3.1':
    MODEL_NAME, MODEL_VERSION = 'Coronium V3.1', '3.1'
    control = active.paths('3.1')
    CHECKPOINT_PATH, ONNX_PATH, MANIFEST_PATH, COMPARISON_PATH = (control[k] for k in ('checkpoint','onnx','manifest','comparison'))
if IS_RELEASE_V32:
    active.load_release()
    RELEASE_MANIFEST = json.loads(MANIFEST_PATH.read_text())
    BACKBONE_DROPOUT = 0.0
    TEST_RUNTIME = 'kleidiai_off'  # Compatibility name; no experimental environment required.
    EVALUATION_PROTOCOL = RELEASE_MANIFEST['evaluation_protocol']
    MODEL_STATUS = ('locally_promoted; seed=42; epoch=27' if active.DEFAULT_VERSION == '3.2' else 'release_staged_not_promoted; seed=42; epoch=27')
FIXED_CPU_EXECUTION = TEST_MODE or IS_RELEASE_V32
CATALOG_PATH = ROOT / 'experiments/v32g_service_integration_v1/catalog.json'
CATALOG_SHA256 = 'bc054445cca3e18e50e2fac18ba24ae037367c16e1756b8a65333b1c270a8b8f'


def verify_file(record):
    path = ROOT / record['path']
    if not path.is_file():
        raise FileNotFoundError(f'Selected serving artifact missing: {path}')
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError(f'Selected serving artifact hash mismatch: {path}')
    return path


def read_catalog():
    verify_file({'path': str(CATALOG_PATH.relative_to(ROOT)), 'sha256': CATALOG_SHA256})
    return json.loads(CATALOG_PATH.read_text())


if TEST_MODE:
    CATALOG = read_catalog()
if IS_CANDIDATE:
    RECORD = CATALOG['models'][TEST_MODEL]
    SEED = RECORD['seed']
    MODEL_NAME = f'Coronium V3.2 candidate C1 seed {SEED}'
    MODEL_VERSION = f'3.2-candidate-c1-s{SEED}'
    MODEL_STATUS = f'candidate_not_promoted; seed={SEED}; epoch={RECORD["epoch"]}'
    CHECKPOINT_PATH, ONNX_PATH = (ROOT / RECORD[k]['path'] for k in ('checkpoint', 'onnx'))
    MANIFEST_PATH = ROOT / RECORD['manifest']['path']
    COMPARISON_PATH = ROOT / RECORD[TEST_RUNTIME + '_predictions']['path']
    BACKBONE_DROPOUT = 0.0
    EVALUATION_PROTOCOL = f'deterministic ONNX CPU FP32 batch1; seed={SEED}; runtime={TEST_RUNTIME}; selection validation, not independent test'


def load_release():
    if not IS_CANDIDATE:
        release = active.load_version('3.1') if TEST_MODE else active.load_release()
        if TEST_MODE and TEST_RUNTIME == 'kleidiai_off':
            ref = CATALOG['V3.1_mitigated']
            saved = json.loads(verify_file(ref['metrics']).read_text())
            verify_file(ref['predictions'])
            release['serving_deterministic'] = dict(release['serving_deterministic'], onnx=saved['metrics']['all'], runtime='kleidiai_off', protocol='deterministic ONNX CPU FP32 batch1; selection validation')
        return release
    read_catalog()
    for key in ['manifest','checkpoint','onnx','config','completion','source_manifest','d_csv',TEST_RUNTIME+'_metrics',TEST_RUNTIME+'_predictions']:
        verify_file(RECORD[key])
    manifest = json.loads(MANIFEST_PATH.read_text())
    config = json.loads((ROOT / RECORD['config']['path']).read_text())
    completion = json.loads((ROOT / RECORD['completion']['path']).read_text())
    if not (manifest['seed'] == config['seed'] == SEED and
            manifest['epoch'] == completion['best_epoch'] == RECORD['epoch'] and
            manifest['promoted'] is False and manifest['dropout_backbone'] == config['dropout_backbone'] == 0 and
            manifest['dropout_head'] == config['dropout_head'] == .3 and manifest['parameters'] == 206875 and
            manifest['input_shape'] == ['N',2,512,512] and manifest['dtype'] == 'float32' and
            manifest['onnx']['sha256'] == RECORD['onnx']['sha256'] and
            manifest['checkpoint']['sha256'] == completion['checkpoint_sha256']['best.pth'] == RECORD['checkpoint']['sha256']):
        raise ValueError('Candidate manifest/configuration mismatch; no fallback permitted')
    saved = json.loads((ROOT / RECORD[TEST_RUNTIME+'_metrics']['path']).read_text())
    groups = saved['metrics'] if TEST_RUNTIME == 'kleidiai_off' else saved['metrics']['onnx']
    overall = groups['all' if TEST_RUNTIME == 'kleidiai_off' else 'global']
    return {'model_version': MODEL_VERSION, 'status': METRICS_STATUS,
            'serving_deterministic': {'protocol': EVALUATION_PROTOCOL, 'onnx': overall, 'groups': groups,
                                     'checkpoint_sha256': RECORD['checkpoint']['sha256'], 'onnx_sha256': RECORD['onnx']['sha256']},
            'historical_v3': active.load_version('3.1')['historical_v3']}


def configure_session_options(options, ort):
    """Apply the sole E.1 mitigation to configured releases or explicit trials."""
    if FIXED_CPU_EXECUTION:
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    if TEST_RUNTIME == 'kleidiai_off':
        # Pin the actually validated native build, not merely an accepted string option.
        import onnxruntime.capi.onnxruntime_pybind11_state as native
        expected = ({'ort_version': RELEASE_MANIFEST['runtime']['ort_version'], 'sha256': RELEASE_MANIFEST['runtime']['native_binary_sha256']} if IS_RELEASE_V32 else CATALOG['binary'])
        if ort.__version__ != expected['ort_version'] or hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest() != expected['sha256']:
            raise ValueError('KleidiAI mitigation not validated for this ORT native binary')
        options.add_session_config_entry('mlas.disable_kleidiai', '1')


def cache_key(filename):
    return (MODEL_VERSION, TEST_RUNTIME, filename) if FIXED_CPU_EXECUTION else filename


def trial_comparison_path():
    return COMPARISON_PATH if (IS_CANDIDATE or IS_RELEASE_V32) else verify_file(CATALOG['V3.1_mitigated']['predictions'])
