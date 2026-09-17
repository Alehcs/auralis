import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACK = HERE.parents[1]


class ReleaseTests(unittest.TestCase):
    def run_python(self, code, version=None, extra=None):
        env = dict(os.environ, PYTHONPATH=str(BACK / 'src'), PYTHONDONTWRITEBYTECODE='1',
                   MPLCONFIGDIR=str(HERE / 'runtime-cache/matplotlib'), XDG_CACHE_HOME=str(HERE / 'runtime-cache'))
        for key in ('AURALIS_RELEASE', 'AURALIS_TEST_MODEL', 'AURALIS_TEST_RUNTIME'):
            env.pop(key, None)
        if version: env['AURALIS_RELEASE'] = version
        env.update(extra or {})
        return subprocess.run([sys.executable, '-B', '-c', code], env=env, cwd=BACK, capture_output=True, text=True)

    def test_default_preserved(self):
        p = self.run_python("from models import serving_selection as s; assert s.MODEL_VERSION=='3.1' and not s.TEST_MODE and not s.FIXED_CPU_EXECUTION; assert s.TEST_RUNTIME=='default'; s.load_release()")
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_staged_release_metrics_and_native_option(self):
        p = self.run_python("""from models import serving_selection as s
import onnxruntime as ort
assert s.MODEL_VERSION=='3.2' and not s.TEST_MODE and s.BACKBONE_DROPOUT==0
assert 'staged_not_promoted' in s.MODEL_STATUS
assert s.load_release()['serving_deterministic']['onnx']['mae']==0.04833447615909939
o=ort.SessionOptions();s.configure_session_options(o,ort)
assert o.get_session_config_entry('mlas.disable_kleidiai')=='1' and o.intra_op_num_threads==4 and o.inter_op_num_threads==1
""", '3.2')
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_unknown_or_conflicting_selection_rejected(self):
        for version, extra in [('bad', {}), ('3.2', {'AURALIS_TEST_MODEL': 'C1_s42'})]:
            p = self.run_python('from models import serving_selection', version, extra)
            self.assertNotEqual(p.returncode, 0)

    def test_corrupt_or_missing_release_fails(self):
        p = self.run_python("""from models import active_model as a
from pathlib import Path
from unittest.mock import patch
original=Path.read_bytes
def corrupt(p):
 return b'corrupt' if p==a.ONNX_PATH else original(p)
with patch.object(Path,'read_bytes',corrupt):
 try:a.load_release()
 except ValueError:pass
 else:raise AssertionError('corruption accepted')
with patch.object(a,'CHECKPOINT_PATH',a.ROOT/'models/missing.pth'):
 try:a.load_release()
 except (OSError,KeyError):pass
 else:raise AssertionError('missing accepted')
""", '3.2')
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_agent_join_and_mc_constructor(self):
        p = self.run_python("""from agents.data_loader import load_agent_dataset
from models.train_model import CoroniumV3
from models import serving_selection as s
import torch
d=load_agent_dataset();assert len(d.validation_rows)==263 and len(d.train_indices)==1051
assert abs(sum(r.error for r in d.validation_rows)/263 - s.load_release()['serving_deterministic']['onnx']['mae'])<1e-12
m=CoroniumV3(in_channels=2,dropout_rate=s.BACKBONE_DROPOUT);m.eval()
for module in m.modules():
 if isinstance(module,(torch.nn.Dropout,torch.nn.Dropout2d)):module.train()
assert m.head_dropout.training and m.head_dropout.p==.3
assert all(not module.training for module in m.modules() if isinstance(module,torch.nn.BatchNorm2d))
assert all(getattr(m,f'stage{i}').dropout.p==0 for i in range(1,5))
m.eval()
""", '3.2')
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_experimental_candidates_still_explicit(self):
        for name in ('V3.1', 'C1_s42', 'C1_s137', 'C1_s2026'):
            p = self.run_python('from models import serving_selection as s; assert s.TEST_MODE; s.load_release()', extra={'AURALIS_TEST_MODEL': name, 'AURALIS_TEST_RUNTIME': 'kleidiai_off'})
            self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == '__main__': unittest.main(verbosity=2)
