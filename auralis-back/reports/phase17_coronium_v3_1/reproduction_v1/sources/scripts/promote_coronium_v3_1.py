"""Create the fixed Phase 1.6 release, without replacing any existing artifact.

Run from auralis-back. The manifest is written last, after export and parity.
Re-running an existing release fails; verification is in verify_phase16.py.
"""

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from models.active_model import CHECKPOINT_PATH, ONNX_PATH, METRICS_PATH, MANIFEST_PATH, COMPARISON_PATH, MODEL_NAME, MODEL_VERSION, METRICS_STATUS
from processing.model_input import prepare_model_input, processed_filename, INPUT_CONTRACT, TARGET_CONTRACT
from processing.scientific_split import load_split, sha256
from export_to_onnx import load_pytorch_model, export_onnx, verify_onnx

RUN = ROOT / "experiments/phase15_runs/20260905T132456995672Z"
REPORT = ROOT / "reports/phase16_coronium_v3_1"


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def copy_new(source, destination):
    with destination.open("xb") as stream:
        stream.write(source.read_bytes())


def metrics(y, pred):
    nonzero = y != 0
    return {"mae": float(mean_absolute_error(y, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, pred))),
            "r2": float(r2_score(y, pred)),
            "mape": float(np.mean(abs((pred[nonzero] - y[nonzero]) / y[nonzero])) * 100)}


def main():
    for path in (CHECKPOINT_PATH, ONNX_PATH, METRICS_PATH, MANIFEST_PATH, COMPARISON_PATH):
        if path.exists():
            raise FileExistsError(path)
    training = json.loads((RUN / "manifest.json").read_text())
    evaluation = json.loads((RUN / "evaluation_clean_v1/manifest.json").read_text())
    verification = json.loads((RUN / "verification.json").read_text())
    checkpoint_hash = sha256(RUN / "best.pth")
    assert checkpoint_hash == "1e4c834451375a7c4a1f47bd60404bf9aec3bc20c18056c9fc1b517b168e8e51"
    assert checkpoint_hash == training["checkpoint_sha256"] == evaluation["weights_sha256"] == verification["checkpoint_sha256"]
    assert training["best_epoch"] == 40 and verification["status"] == "verified"
    assert verification["same_predictions_in_two_processes"] and verification["observation_overlap"] == 0
    assert evaluation["evaluation_completed"] and evaluation["validation_observations"] == 263
    for source, digest in training["source_sha256"].items():
        assert sha256(Path(source)) == digest, source
    csv = ROOT / "data/processed/metadata_processed.csv"
    split_path = ROOT / "models/split_indices_phase1_v1.json"
    split = load_split(split_path, csv)
    assert sha256(split_path) == evaluation["split_sha256"] == training["split_sha256"]
    assert sha256(csv) == evaluation["metadata_sha256"]
    preserved = json.loads((REPORT / "preserved_before.json").read_text())
    for name, digest in preserved.items():
        assert sha256(ROOT / name) == digest, name

    torch.set_num_threads(4)
    torch.manual_seed(42)
    copy_new(RUN / "best.pth", CHECKPOINT_PATH)
    model = load_pytorch_model(CHECKPOINT_PATH)
    export_onnx(model, ONNX_PATH)
    verify_onnx(ONNX_PATH)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    session = ort.InferenceSession(str(ONNX_PATH), sess_options=options, providers=["CPUExecutionProvider"])
    name = session.get_inputs()[0].name
    metadata = pd.read_csv(csv)
    rows = []
    for count, index in enumerate(split["val"]):
        row = metadata.iloc[index]
        filename = processed_filename(row)
        x = prepare_model_input(np.load(ROOT / "data/processed" / filename, allow_pickle=False))[None]
        with torch.inference_mode():
            pt = float(model(torch.from_numpy(x)).item())
        onnx_pred = float(session.run(None, {name: x})[0].item())
        np.testing.assert_allclose(onnx_pred, pt, atol=1e-5, rtol=1e-5)
        rows.append({"source_row": index, "processed_file": filename,
                     "target_si": float(np.float32(row.sunspot_index)),
                     "pytorch_si": pt, "onnx_si": onnx_pred,
                     "abs_difference": abs(pt - onnx_pred)})
        if (count + 1) % 50 == 0:
            print(f"Deterministic validation parity: {count + 1}/263", flush=True)
    # Explicitly exercise the exported dynamic batch dimension.
    batch = np.repeat(x, 2, axis=0)
    with torch.inference_mode():
        expected = model(torch.from_numpy(batch)).numpy()
    np.testing.assert_allclose(session.run(None, {name: batch})[0], expected, atol=1e-5, rtol=1e-5)
    frame = pd.DataFrame(rows)
    deterministic_csv = REPORT / "coronium_v3_1_deterministic_predictions.csv"
    frame.to_csv(deterministic_csv, index=False, mode="x")
    mc_predictions = REPORT / "coronium_v3_1_mc_predictions.csv"
    copy_new(RUN / "evaluation_clean_v1/predictions.csv", mc_predictions)
    copy_new(RUN / "evaluation_clean_v1/results_comparison.csv", COMPARISON_PATH)
    mc = pd.read_csv(mc_predictions, float_precision="round_trip")
    assert mc.source_row.tolist() == split["val"]
    assert mc.processed_file.tolist() == frame.processed_file.tolist()
    np.testing.assert_array_equal(mc.target_si, frame.target_si)
    for key, value in metrics(mc.target_si.to_numpy(), mc.prediction_si.to_numpy()).items():
        np.testing.assert_allclose(value, evaluation["metrics"][key], atol=2e-6, rtol=1e-6)
    report = {
        "model_name": MODEL_NAME, "model_version": MODEL_VERSION,
        "status": METRICS_STATUS, "validation_observations": 263, "observation_overlap": 0,
        "units": "SI percentage points (MAE/RMSE), dimensionless R2, percent MAPE",
        "checkpoint_sha256": checkpoint_hash,
        "official_mc_dropout": {"protocol": "MC Dropout T=20, seed=42, batch=32, MPS; Phase 1.5",
                                "metrics": evaluation["metrics"], "source": str((RUN / "evaluation_clean_v1/manifest.json").relative_to(ROOT))},
        "serving_deterministic": {"protocol": "single eval-mode pass, CPU, batch=1; no input noise in point estimate",
                                  "pytorch": metrics(frame.target_si.to_numpy(), frame.pytorch_si.to_numpy()),
                                  "onnx": metrics(frame.target_si.to_numpy(), frame.onnx_si.to_numpy())},
        "historical_v3": {"model_name": "Coronium V3 PRO", "status": "historical_contaminated_validation_not_generalization_evidence",
                          "source": "experiments/exp_005_v3pro_augmented.json", "validation_rows": 353, "observation_overlap": 145,
                          "metrics": {"mae": 0.1048, "rmse": 0.1272, "r2": 0.8634, "mape": 6.07}},
        "scope": "Validation used for checkpoint selection and early stopping; not an untouched test or temporal generalization. MC metrics are not single-pass API metrics.",
    }
    write_json(METRICS_PATH, report)
    artifacts = [CHECKPOINT_PATH, ONNX_PATH, METRICS_PATH, COMPARISON_PATH, mc_predictions, deterministic_csv]
    sources = [RUN / name for name in ("best.pth", "manifest.json", "verification.json", "phase15_protocol.json", "environment.json", "history.json", "evaluation_clean_v1/manifest.json", "evaluation_clean_v1/predictions.csv")]
    sources += [split_path, csv, ROOT / "src/models/train_model.py", ROOT / "src/processing/model_input.py", Path(__file__).resolve(), ROOT / "scripts/export_to_onnx.py"]
    for path, digest in preserved.items():
        assert sha256(ROOT / path) == digest, path
    write_json(MANIFEST_PATH, {
        "model_name": MODEL_NAME, "model_version": MODEL_VERSION, "status": "promoted",
        "created_utc": datetime.now(timezone.utc).isoformat(), "source_run": str(RUN.relative_to(ROOT)),
        "best_epoch": 40, "parameters": sum(p.numel() for p in model.parameters()),
        "input_contract": INPUT_CONTRACT, "target_contract": TARGET_CONTRACT,
        "onnx_export": {"opset": 18, "mode": "eval", "dynamic_batch": True, "external_data": False, "bytes": ONNX_PATH.stat().st_size},
        "artifacts_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in artifacts},
        "sources_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sources},
        "environment": {"python": platform.python_version(), "torch": torch.__version__, "onnxruntime": ort.__version__, "platform": platform.platform()},
        "export_parity": {"observations": len(frame), "atol": 1e-5, "rtol": 1e-5, "max_abs_difference": float(frame.abs_difference.max()), "dynamic_batch_2": "passed"},
        "preserved_artifacts": len(preserved),
    })
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
