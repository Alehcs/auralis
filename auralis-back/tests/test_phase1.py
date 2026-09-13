"""Directed Phase 1 regression checks; no training and no artifact replacement."""

import asyncio
import builtins
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from api import main as api
from models.train_model import SolarDataset, CoroniumV3, train_model
from processing.model_input import prepare_model_input, processed_filename
from processing.observation_time import filename_time
from processing.scientific_split import build_split, load_split, sha256, validate_split
import evaluate_final
import test_inference


class Phase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        cls.csv = ROOT / "data/processed/metadata_processed.csv"
        cls.data = ROOT / "data/processed"
        cls.dataset = SolarDataset(str(cls.data), str(cls.csv))
        cls.evidence = json.loads((ROOT / "reports/phase1_v1/evidence.json").read_text())

    def test_split_zero_overlap_and_reproducible_deduplication(self):
        split = load_split(ROOT / "models/split_indices_phase1_v1.json", self.csv)
        self.assertEqual(split, build_split(self.csv, ROOT / "models/split_indices.json"))
        self.assertEqual((len(split["train"]), len(split["val"])), (1051, 263))
        rows = [i for group in split["observation_rows"].values() for i in group]
        self.assertEqual(sorted(rows), list(range(1763)))
        ids = self.dataset.metadata.apply(processed_filename, axis=1)
        self.assertEqual(set(ids.iloc[split["train"]]) & set(ids.iloc[split["val"]]), set())
        broken = dict(split, val=[split["train"][0]] + split["val"])
        with self.assertRaises(ValueError):
            validate_split(broken, self.csv)

    def test_conflicting_duplicates_and_changed_csv_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            csv = Path(folder) / "metadata.csv"
            frame = self.dataset.metadata.copy()
            ids = frame.apply(processed_filename, axis=1)
            duplicate = ids.index[ids.duplicated()][0]
            frame.loc[duplicate, "sunspot_index"] += 0.1
            frame.to_csv(csv, index=False)
            with self.assertRaises(ValueError):
                build_split(csv, ROOT / "models/split_indices.json")
            with self.assertRaises(ValueError):
                load_split(ROOT / "models/split_indices_phase1_v1.json", csv)

    def test_all_real_inputs_match_training_evaluation_and_api(self):
        ids = self.dataset.metadata.apply(processed_filename, axis=1)
        for index in ids.index[~ids.duplicated()]:
            data = np.load(self.data / ids[index], allow_pickle=False)
            tensor, target = self.dataset[int(index)]
            expected = np.stack([np.maximum(data, 0), np.maximum(-data, 0)])
            np.testing.assert_array_equal(tensor.numpy(), expected)
            np.testing.assert_array_equal(api._prepare_numpy(data)[0], tensor.numpy())
            np.testing.assert_array_equal(api._prepare_tensor(data, torch.device("cpu"))[0], tensor)
            np.testing.assert_array_equal(test_inference.load_image(self.data, ids[index]), expected)
            self.assertEqual(target.item(), np.float32(self.dataset.metadata.iloc[index].sunspot_index))
        with patch.object(evaluate_final, "DATA_DIR", self.data), patch.object(evaluate_final, "METADATA_CSV", self.csv):
            loader = evaluate_final.build_val_loader(ROOT / "models/split_indices_phase1_v1.json")
            x, _ = loader.dataset[0]
            source_index = loader.dataset.indices[0]
            np.testing.assert_array_equal(x, api._prepare_numpy(np.load(self.data / ids[source_index]))[0])

    def test_input_rejects_wrong_representation(self):
        for bad in (np.zeros((4, 4)), np.full((512, 512), np.nan),
                    np.full((512, 512), 400), np.ones((2, 512, 512)),
                    np.full((2, 512, 512), -0.1)):
            with self.assertRaises(ValueError):
                prepare_model_input(bad)

    def test_tai_utc_leap_seconds_and_original_preserved(self):
        cases = {
            "2016.02.03_00_01_30": "2016-02-03T00:00:54.000Z",
            "2024.01.01_00_01_30": "2024-01-01T00:00:53.000Z",
            "2017.01.01_00_00_36": "2016-12-31T23:59:60.000Z",
            "2017.01.01_00_00_37": "2017-01-01T00:00:00.000Z",
        }
        for value, expected in cases.items():
            result = filename_time(f"hmi.m_45s.{value}_TAI.magnetogram_processed.npy")
            self.assertEqual(result["date"], expected)
            self.assertEqual(result["date_scale"], "TAI")
            self.assertFalse(result["date_original"].endswith("Z"))
        self.assertIsNone(filename_time("no-time.npy")["date"])
        times = json.loads((ROOT / "reports/phase1_v1/observation_times.json").read_text())
        self.assertTrue(all(t["csv_date_scale"] == "unknown_not_recorded" for t in times.values()))

    def test_no_astropy_never_labels_tai_as_utc(self):
        real_import = builtins.__import__
        def without_astropy(name, *args, **kwargs):
            if name == "astropy.time":
                raise ImportError("lean API environment")
            return real_import(name, *args, **kwargs)
        filename_time.cache_clear()
        with patch("builtins.__import__", side_effect=without_astropy):
            result = filename_time("hmi.m_45s.2025.01.01_00_01_30_TAI.npy")
        self.assertIsNone(result["date"])
        self.assertIsNone(result["date_utc"])
        self.assertEqual(result["date_scale"], "TAI")
        filename_time.cache_clear()

    def test_new_fits_preparation_raw_si_and_time_scale(self):
        from types import SimpleNamespace
        from astropy.time import Time
        from processing.prepare_dataset import load_and_process_magnetogram
        from predict import preprocess_fits_image
        # Strictly >200 G, two of four ORIGINAL pixels, including one NaN.
        field = np.array([[201., -201.], [200., np.nan]], dtype=np.float32)
        solar_map = SimpleNamespace(data=field, date=Time("2024-01-01T00:01:30", scale="tai"))
        with patch("sunpy.map.Map", return_value=solar_map):
            image, meta = load_and_process_magnetogram(Path("fixture.fits"))
            cli_tensor, _ = preprocess_fits_image(Path("fixture.fits"))
        self.assertEqual(meta["sunspot_index"], 50.0)
        self.assertEqual(meta["date_scale"], "TAI")
        self.assertEqual(meta["date_utc"], "2024-01-01T00:00:53.000Z")
        np.testing.assert_array_equal(image, cli_tensor[0])

    def test_preserved_scientific_artifacts_and_npy_hashes(self):
        for name, digest in self.evidence["preserved_artifact_sha256"].items():
            self.assertEqual(sha256(ROOT / name), digest, name)
        for name, digest in self.evidence["npy_sha256"].items():
            self.assertEqual(sha256(self.data / name), digest, name)

    def test_checkpoint_and_onnx_parity(self):
        import onnxruntime as ort
        model = CoroniumV3(in_channels=2, dropout_rate=0.2)
        model.load_state_dict(torch.load(ROOT / "models/best_coronium_v3_pro_augmented.pth",
                                         map_location="cpu", weights_only=True))
        model.eval()
        options = ort.SessionOptions(); options.intra_op_num_threads = 2
        session = ort.InferenceSession(str(ROOT / "models/best_coronium_v3_pro.onnx"),
                                       sess_options=options, providers=["CPUExecutionProvider"])
        for index in (0, 600, 1700):
            x, _ = self.dataset[index]
            with torch.no_grad():
                expected = model(x[None]).numpy()
            actual = session.run(None, {session.get_inputs()[0].name: x.numpy()[None]})[0]
            np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-5)
        # Exercise all three serving entrypoints with the real ONNX graph.
        from fastapi import UploadFile
        name = processed_filename(self.dataset.metadata.iloc[0])
        with patch.object(api, "_ort_session", session), patch.object(api, "_ort_input_name", session.get_inputs()[0].name), patch.object(api, "_predict_cache", {}):
            prediction = asyncio.run(api.predict(name))
            alias = asyncio.run(api.predict_dual(name))
            upload = asyncio.run(api.predict_upload(UploadFile(filename=name, file=io.BytesIO((self.data / name).read_bytes()))))
        self.assertEqual(prediction, alias)
        self.assertEqual(prediction, upload)
        self.assertIn("heuristic", prediction.confidence_method)
        self.assertIn("synthetic", prediction.uncertainty_method)

    def test_demo_labels_and_catalog(self):
        stats = asyncio.run(api.get_stats())
        self.assertIn("clean_observation_validation", stats.metrics_status)
        self.assertIn("contaminated", stats.historical_v3["status"])
        catalog = asyncio.run(api.list_images())
        self.assertEqual(catalog.total, 1314)
        self.assertTrue(all(item.date_scale == "TAI" for item in catalog.images))
        name = catalog.images[0].filename
        with tempfile.TemporaryDirectory() as directory, patch.object(api, "AIA_DIR", Path(directory)):
            image = asyncio.run(api.get_aia_image(name))
        self.assertEqual(image.headers["x-auralis-image-source"], "synthetic_hmi_proxy")

    def test_existing_checkpoint_and_report_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.pth"
            path.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                train_model(torch.nn.Linear(1, 1), [], [], device=torch.device("cpu"), checkpoint_path=path)
            self.assertEqual(path.read_bytes(), b"preserve")
            with self.assertRaises(FileExistsError):
                evaluate_final.export_comparison_csv(np.array([1.]), np.array([1.]), path)

    def test_http_lifecycle_schemas_and_gradcam(self):
        from fastapi.testclient import TestClient
        with TestClient(api.app) as client:
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertTrue(health.json()["model_loaded"])
            catalog = client.get("/api/images/list")
            self.assertEqual(catalog.status_code, 200)
            name = catalog.json()["images"][0]["filename"]
            self.assertEqual(client.get("/api/stats").status_code, 200)
            self.assertEqual(client.get(f"/api/predict/{name}").status_code, 200)
            layers = client.get(f"/api/explain-layers/{name}")
            self.assertEqual(layers.status_code, 200)
            self.assertEqual(len(layers.json()), 3)
            self.assertTrue(all("not area" in layer["activation_interpretation"] for layer in layers.json()))
            buf = io.BytesIO(); np.save(buf, np.full((512, 512), 400, dtype=np.float32))
            invalid = client.post("/api/predict-upload", files={"file": ("raw-gauss.npy", buf.getvalue())})
            self.assertEqual(invalid.status_code, 422)

    def test_evaluation_does_not_validate_old_weights_on_new_split_by_default(self):
        with patch.object(sys, "argv", ["evaluate_final.py"]):
            with self.assertRaises(SystemExit) as error:
                evaluate_final.main()
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
