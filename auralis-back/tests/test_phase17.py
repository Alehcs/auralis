"""Scientific regression guards for Phase 1.7 reports and protocol selection."""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from run_phase17 import align_predictions, activity_bands, summarize
from plot_final_scatter import load_report
from processing.scientific_split import sha256
from api import main as api

REPORT = ROOT / "reports/phase17_coronium_v3_1/analysis_v2"


class Phase17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_report(REPORT)
        cls.metrics = json.loads((REPORT / "metrics.json").read_text())
        cls.metadata = pd.read_csv(ROOT / "data/processed/metadata_processed.csv")
        cls.split = json.loads((ROOT / "models/split_indices_phase1_v1.json").read_text())
        folder = ROOT / "reports/phase16_coronium_v3_1"
        cls.mc = pd.read_csv(folder / "coronium_v3_1_mc_predictions.csv", float_precision="round_trip")
        cls.det = pd.read_csv(folder / "coronium_v3_1_deterministic_predictions.csv", float_precision="round_trip")

    def test_metrics_independent_sklearn_calculation(self):
        y = self.data.target_si.to_numpy()
        for key, values in self.metrics["metrics"].items():
            prediction = self.data[key].to_numpy()
            self.assertAlmostEqual(values["mae"], mean_absolute_error(y, prediction), places=12)
            self.assertAlmostEqual(values["rmse"], np.sqrt(mean_squared_error(y, prediction)), places=12)
            self.assertAlmostEqual(values["r2"], r2_score(y, prediction), places=12)
            self.assertAlmostEqual(values["mape"], np.mean(abs((prediction-y)/y))*100, places=12)

    def test_target_boundaries_and_empty_constant_zero_targets(self):
        self.assertEqual(activity_bands([1.4099, 1.41, 1.7499, 1.75]).tolist(), ['low', 'medium', 'medium', 'high'])
        empty = summarize([], [])
        self.assertEqual(empty['n'], 0); self.assertIsNone(empty['r2'])
        zero = summarize([0, 0], [1, 1])
        self.assertEqual(zero['mae'], 1); self.assertIsNone(zero['mape']); self.assertIsNone(zero['r2'])
        with self.assertRaises(ValueError):
            summarize([1, float('nan')], [1, 2])

    def test_alignment_rejects_reordering_duplicates_and_target_drift(self):
        for broken in (self.mc.iloc[::-1], self.mc.iloc[:-1], self.mc.assign(target_si=self.mc.target_si + .01),
                       self.mc.assign(processed_file=self.mc.processed_file.iloc[0])):
            with self.assertRaises(ValueError):
                align_predictions(broken, self.det, self.metadata, self.split)
        self.assertEqual(len(align_predictions(self.mc, self.det, self.metadata, self.split)), 263)

    def test_baseline_is_training_only(self):
        mean = self.metadata.iloc[self.split['train']].sunspot_index.to_numpy(dtype=np.float32).astype(np.float64).mean()
        self.assertEqual(self.metrics['constant_baseline']['mean_si'], mean)
        self.assertFalse(np.isclose(mean, self.data.target_si.mean(), rtol=1e-6))
        np.testing.assert_array_equal(self.data.train_mean_si, np.full(263, mean))

    def test_band_aggregation_reconstructs_global_mae_and_bias(self):
        bands = pd.read_csv(REPORT / 'metrics_by_activity.csv')
        for protocol, rows in bands.groupby('protocol'):
            self.assertEqual(rows.n.sum(), 263)
            for metric in ('mae', 'bias'):
                self.assertAlmostEqual(np.average(rows[metric], weights=rows.n), self.metrics['metrics'][protocol][metric], places=12)

    def test_worst_cases_ranked_independently_and_dates_labeled(self):
        worst = pd.read_csv(REPORT / 'worst_cases.csv')
        for key in ('mc_si', 'onnx_si'):
            rows = worst[worst.protocol == key]
            expected = self.data.sort_values(key+'_absolute_error', ascending=False, kind='stable').head(10)
            self.assertEqual(rows.source_row.tolist(), expected.source_row.tolist())
            self.assertTrue((rows.csv_date_scale == 'unknown').all())
            self.assertTrue(rows.record_time_utc.str.endswith('Z').all())

    def test_api_protocol_default_and_selection_match_real_csv(self):
        for key, param in [('mc_si', 'mc'), ('onnx_si', 'deterministic')]:
            points = asyncio.run(api.get_results_comparison(param))
            self.assertEqual(len(points), 263)
            np.testing.assert_allclose([p['predicted'] for p in points], self.data[key], atol=1e-6)
            self.assertTrue(all(p['model_version'] == '3.1' for p in points))
            self.assertIn('selection', points[0]['evaluation_protocol'])
        self.assertEqual(asyncio.run(api.get_results_comparison()), asyncio.run(api.get_results_comparison('mc')))
        with self.assertRaises(HTTPException) as error:
            asyncio.run(api.get_results_comparison('mixed'))
        self.assertEqual(error.exception.status_code, 422)

    def test_corrupt_evaluation_rejected_in_api(self):
        original = Path.read_bytes
        def corrupt(path):
            return b'corrupt' if path.name == 'coronium_v3_1_deterministic_predictions.csv' else original(path)
        with patch.object(Path, 'read_bytes', corrupt):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(api.get_results_comparison('deterministic'))
        self.assertEqual(error.exception.status_code, 503)

    def test_historical_benchmark_excludes_v31_claim(self):
        result = asyncio.run(api.get_benchmark())
        self.assertFalse(result.comparison_valid_for_v31)
        self.assertIn('historical', result.proposed.name)
        self.assertIn('352 versus 353', result.comparison_note)

    def test_all_report_outputs_and_source_snapshots_have_intact_hashes(self):
        manifest = json.loads((REPORT / 'manifest.json').read_text())
        for name, digest in manifest['outputs_sha256'].items():
            self.assertEqual(sha256(REPORT / name), digest, name)
        for name, digest in manifest['sources_sha256'].items():
            self.assertEqual(sha256(ROOT / name), digest, name)
        figures = list((REPORT / 'figures').glob('*.png'))
        self.assertEqual(len(figures), 13)
        for figure in figures:
            for extension in ('.pdf', '.svg'):
                self.assertTrue(figure.with_suffix(extension).exists())

    def test_latency_raw_samples_and_quantiles(self):
        latency = json.loads((REPORT / 'latency.json').read_text())
        self.assertEqual(latency['checkpoint_sha256'], self.metrics['artifacts']['files']['models/best_coronium_v3_1.pth']['sha256'])
        for key, result in latency['summary'].items():
            samples = [r['latency_ms'] for r in latency['raw_measurements'] if r['protocol'] == key]
            self.assertEqual(len(samples), 60)
            self.assertTrue(all(x > 0 for x in samples))
            self.assertAlmostEqual(result['median_ms'], np.median(samples))
            self.assertAlmostEqual(result['p95_ms'], np.quantile(samples, .95))
        self.assertIn('HTTP', latency['scope'])
        self.assertIn('accuracy', latency['mc_note'])

    def test_historical_model_training_and_protected_files_preserved(self):
        before = json.loads((REPORT.parent / 'audit_before.json').read_text())
        count = 0
        for name, digest in before.items():
            frozen = name.startswith(('auralis-back/experiments/', 'auralis-back/models/', 'auralis-back/reports/'))
            protected = any(x in name.lower() for x in ('unity', 'webar', 'timeline', '/simulation/', 'digital-twin', 'agent-lab', 'src/agents/', 'agent_routes'))
            if frozen or protected:
                self.assertEqual(sha256(ROOT.parent / name), digest, name)
                count += 1
        self.assertGreater(count, 100)


if __name__ == '__main__':
    unittest.main()
