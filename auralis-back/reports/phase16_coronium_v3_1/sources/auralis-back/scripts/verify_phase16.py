"""Verify V3.1 provenance, real HTTP inference and preservation; no retraining.

Use --output with a fresh filename to preserve earlier verification evidence.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from api import main as api
from models.active_model import load_release, MANIFEST_PATH, CHECKPOINT_PATH
from processing.scientific_split import sha256
from predict import load_model

REPORT = ROOT / "reports/phase16_coronium_v3_1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPORT / "verification.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    torch.set_num_threads(4)
    release = load_release()
    manifest = json.loads(MANIFEST_PATH.read_text())
    for group in ("artifacts_sha256", "sources_sha256"):
        for name, digest in manifest[group].items():
            assert sha256(ROOT / name) == digest, name
    preserved = json.loads((REPORT / "preserved_before.json").read_text())
    for name, digest in preserved.items():
        assert sha256(ROOT / name) == digest, name
    before = json.loads((REPORT / "workspace_before.json").read_text())
    protected = {name: digest for name, digest in before.items()
                 if any(part in name.lower() for part in ("unity", "webar", "timeline", "agent-lab", "src/agents/", "agent_routes", "/simulation/", "digital-twin"))}
    for name, digest in protected.items():
        assert sha256(ROOT.parent / name) == digest, name

    frame = pd.read_csv(REPORT / "coronium_v3_1_deterministic_predictions.csv", float_precision="round_trip")
    # Predeclared quantiles of targets plus temporal endpoints, not chosen by error.
    ordered = frame.sort_values("target_si")
    selected = ordered.iloc[np.linspace(0, len(frame) - 1, 9).astype(int)]
    selected = pd.concat([selected, frame.sort_values("processed_file").iloc[[0, -1]]]).drop_duplicates("source_row")
    cli_model, _ = load_model(str(CHECKPOINT_PATH), torch.device("cpu"))
    logging.getLogger("httpx").setLevel(logging.WARNING)
    comparisons = []
    with TestClient(api.app) as client:
        health = client.get("/health").json()
        assert health["model_loaded"] and health["model_version"] == "3.1"
        assert health["checkpoint"] == CHECKPOINT_PATH.name
        stats_response = client.get("/api/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["model_version"] == "3.1" and stats["observation_overlap"] == 0
        assert stats["mae"] == release["official_mc_dropout"]["metrics"]["mae"]
        assert stats["serving_deterministic"] == release["serving_deterministic"]
        assert stats["historical_v3"]["metrics"]["mae"] == 0.1048
        scatter = client.get("/api/results-comparison").json()
        assert len(scatter) == 263 and all(p["model_version"] == "3.1" for p in scatter)
        mc = pd.read_csv(REPORT / "coronium_v3_1_mc_predictions.csv", float_precision="round_trip")
        np.testing.assert_allclose([p["predicted"] for p in scatter], mc.prediction_si, atol=1e-6)
        benchmark = client.get("/api/benchmark").json()
        assert "historical" in benchmark["proposed"]["name"]
        assert benchmark["proposed"]["mae"] == 0.1048
        for _, row in selected.iterrows():
            name = row.processed_file
            path = api.DATA_DIR / name
            x = api._prepare_numpy(np.load(path, allow_pickle=False))
            with torch.inference_mode():
                cpu = float(cli_model(torch.from_numpy(x)).item())
                resident = float(api._model(torch.from_numpy(x).to(api._device)).item())
            onnx_value = float(api._ort_session.run(None, {api._ort_input_name: x})[0].item())
            np.testing.assert_allclose([resident, onnx_value, row.pytorch_si], cpu, atol=1e-5, rtol=1e-5)
            response = client.get(f"/api/predict/{name}")
            assert response.status_code == 200
            result = response.json()
            assert result["model_version"] == "3.1"
            assert result["sunspot_index"] == round(onnx_value, 4)
            assert abs(result["sunspot_index"] - cpu) <= 5e-5 + 1e-5
            alias = client.get(f"/api/predict-dual/{name}")
            upload = client.post("/api/predict-upload", files={"file": (name, path.read_bytes(), "application/octet-stream")})
            assert alias.status_code == upload.status_code == 200
            assert alias.json() == upload.json() == result
            assert client.get(f"/api/predict/{name}").json() == result
            comparisons.append({"source_row": int(row.source_row), "filename": name,
                                "pytorch_cpu": cpu, "pytorch_api_device": resident,
                                "onnx_cpu": onnx_value, "http_api": result["sunspot_index"],
                                "alias_upload_cached_equal": True})
    output = {"status": "verified", "model_name": "Coronium V3.1",
              "health": health, "full_validation_export_parity": manifest["export_parity"],
              "http_samples": len(comparisons), "sample_selection": "9 target quantiles plus earliest/latest validation observations",
              "raw_tolerance": {"atol": 1e-5, "rtol": 1e-5}, "http_rounding_decimals": 4,
              "max_pytorch_api_device_difference": max(abs(r["pytorch_cpu"] - r["pytorch_api_device"]) for r in comparisons),
              "max_pytorch_http_difference": max(abs(r["pytorch_cpu"] - r["http_api"]) for r in comparisons),
              "preserved_artifacts": len(preserved), "protected_files_unchanged": len(protected),
              "stats_scatter_and_historical_benchmark": "passed", "comparisons": comparisons}
    with args.output.open("x") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in output.items() if k != "comparisons"}, indent=2))


if __name__ == "__main__":
    main()
