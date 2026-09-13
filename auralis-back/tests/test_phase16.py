"""Release guards: prevent serving mixed V3/V3.1 or replacing exported graphs."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from models import active_model
from export_to_onnx import export_onnx


class Phase16Tests(unittest.TestCase):
    def test_release_declares_distinct_evaluation_protocols(self):
        release = active_model.load_release()
        self.assertEqual(release["model_version"], "3.1")
        self.assertEqual(release["validation_observations"], 263)
        self.assertEqual(release["observation_overlap"], 0)
        self.assertIn("not_independent_test", release["status"])
        self.assertNotEqual(release["official_mc_dropout"]["metrics"], release["serving_deterministic"]["onnx"])
        self.assertIn("contaminated", release["historical_v3"]["status"])

    def test_mixed_or_corrupt_onnx_is_rejected(self):
        original = Path.read_bytes
        def mixed(path):
            return b"wrong weights" if path == active_model.ONNX_PATH else original(path)
        with patch.object(Path, "read_bytes", mixed):
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                active_model.load_release()

    def test_export_refuses_existing_graph_and_external_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.onnx"
            path.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                export_onnx(None, path)
            self.assertEqual(path.read_bytes(), b"preserve")
            sidecar = Path(folder) / "other.onnx.data"
            sidecar.write_bytes(b"preserve data")
            with self.assertRaises(FileExistsError):
                export_onnx(None, Path(folder) / "other.onnx")
            self.assertEqual(sidecar.read_bytes(), b"preserve data")
