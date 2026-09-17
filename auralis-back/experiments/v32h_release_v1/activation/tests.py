"""Reuse release checks, adapting only the two assertions changed by authorized activation."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('prepared_checks',Path(__file__).resolve().parents[1]/'test_release.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class ActivatedReleaseTests(base.ReleaseTests):
 def test_default_preserved(self):
  p=self.run_python("from models import serving_selection as s; assert s.MODEL_VERSION=='3.2' and not s.TEST_MODE and s.FIXED_CPU_EXECUTION; assert s.TEST_RUNTIME=='kleidiai_off'; assert 'locally_promoted' in s.MODEL_STATUS; s.load_release()")
  self.assertEqual(p.returncode,0,p.stderr)
  rollback=self.run_python("from models import serving_selection as s; assert s.MODEL_VERSION=='3.1' and not s.FIXED_CPU_EXECUTION and s.TEST_RUNTIME=='default'; s.load_release()",'3.1')
  self.assertEqual(rollback.returncode,0,rollback.stderr)
 def test_staged_release_metrics_and_native_option(self):
  p=self.run_python("""from models import serving_selection as s
import onnxruntime as ort
assert s.MODEL_VERSION=='3.2' and not s.TEST_MODE and s.BACKBONE_DROPOUT==0
assert 'locally_promoted' in s.MODEL_STATUS
assert s.load_release()['serving_deterministic']['onnx']['mae']==0.04833447615909939
o=ort.SessionOptions();s.configure_session_options(o,ort)
assert o.get_session_config_entry('mlas.disable_kleidiai')=='1' and o.intra_op_num_threads==4 and o.inter_op_num_threads==1
""")
  self.assertEqual(p.returncode,0,p.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
