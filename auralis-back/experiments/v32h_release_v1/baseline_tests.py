"""Reuse seven existing read-only V3.1 regression tests; no inference/export."""
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACK = HERE.parents[1]
os.environ['MPLCONFIGDIR'] = str(HERE / 'runtime-cache/matplotlib')
os.environ['XDG_CACHE_HOME'] = str(HERE / 'runtime-cache')
sys.path.insert(0, str(BACK / 'tests'))
from test_phase16 import Phase16Tests
from test_phase17 import Phase17Tests

names = ['test_api_protocol_default_and_selection_match_real_csv',
         'test_corrupt_evaluation_rejected_in_api',
         'test_historical_benchmark_excludes_v31_claim',
         'test_band_aggregation_reconstructs_global_mae_and_bias']
suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromTestCase(Phase16Tests),
    unittest.TestSuite(Phase17Tests(name) for name in names),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
