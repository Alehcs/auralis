"""Audit local evidence and create an additive, reproducible Phase 1 split.

Run from auralis-back: python scripts/audit_phase1.py
Existing outputs must match byte-for-byte; this script never replaces them.
"""

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from processing.model_input import processed_filename, prepare_model_input
from processing.observation_time import filename_time
from processing.scientific_split import build_split, sha256


def preserve_json(path: Path, value: dict) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text() != text:
            raise FileExistsError(f"Evidence changed; choose a new version instead of replacing {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-diagnostic", action="store_true",
                        help="Compare target interpretations on 16 deterministic CPU samples")
    args = parser.parse_args()
    csv = ROOT / "data/processed/metadata_processed.csv"
    old = ROOT / "models/split_indices.json"
    frame = pd.read_csv(csv)
    ids = frame.apply(processed_filename, axis=1)
    split = build_split(csv, old)
    files = {}; shapes = {}; times = {}
    for name in ids.drop_duplicates():
        path = csv.parent / name
        data = np.load(path, allow_pickle=False)
        prepare_model_input(data)
        row = frame.loc[ids == name].iloc[0]
        if not np.isclose(data.mean(), row.mean_value, atol=1e-9):
            raise ValueError(f"Array/metadata mean differs: {name}")
        files[name] = sha256(path)
        shape = str((data.shape, str(data.dtype)))
        shapes[shape] = shapes.get(shape, 0) + 1
        times[name] = {**filename_time(name), "csv_date_original": row.date,
                       "csv_date_scale": "unknown_not_recorded",
                       "csv_date_source": "solar_map.date.iso (historical code)"}
    if len(set(files.values())) != len(files):
        raise ValueError("Different filenames share identical content; review observation identity")
    lattice = frame.sunspot_index.to_numpy() * 4096**2 / 100
    historic = json.loads(old.read_text())
    report = pd.read_csv(ROOT / "reports/results_comparison.csv")
    errors = report.Predicted_SSN - report.Real_SSN
    artifacts = [csv, *sorted((ROOT / "models").glob("*")),
                 *sorted((ROOT / "experiments").glob("*.json")),
                 ROOT / "reports/results_comparison.csv"]
    artifacts = [p for p in artifacts if p.is_file() and "phase1" not in p.name]
    evidence = {
        "rows": len(frame), "unique_files": len(files), "array_shapes": shapes,
        "legacy_overlap_observations": split["legacy_overlap_observations"],
        "legacy_validation_leaked_rows": split["legacy_validation_leaked_rows"],
        "corrected_train_observations": len(split["train"]),
        "corrected_validation_observations": len(split["val"]),
        "corrected_overlap_observations": 0,
        "target_min": float(frame.sunspot_index.min()),
        "target_max": float(frame.sunspot_index.max()),
        "target_mean": float(frame.sunspot_index.mean()),
        "target_population_std": float(frame.sunspot_index.std(ddof=0)),
        "max_raw_pixel_count_lattice_error": float(np.max(np.abs(lattice - np.round(lattice)))),
        "stored_report_max_target_difference_from_legacy_validation": float(np.max(np.abs(
            report.Real_SSN.to_numpy() - frame.sunspot_index.iloc[historic["val"]].to_numpy()))),
        "stored_csv_metrics_historical_only": {
            "mae": float(abs(errors).mean()), "rmse": float(np.sqrt((errors**2).mean())),
            "r2": float(1 - (errors**2).sum() / ((report.Real_SSN-report.Real_SSN.mean())**2).sum()),
        },
        "preserved_artifact_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in artifacts},
        "npy_sha256": files,
        "runtime_versions": {name: importlib.metadata.version(name) for name in
                             ("numpy", "pandas", "torch", "torchvision", "onnxruntime", "astropy", "scikit-learn")},
    }
    preserve_json(ROOT / "models/split_indices_phase1_v1.json", split)
    preserve_json(ROOT / "reports/phase1_v1/evidence.json", evidence)
    preserve_json(ROOT / "reports/phase1_v1/observation_times.json", times)
    print(json.dumps({key: value for key, value in evidence.items()
                      if key not in ("npy_sha256", "preserved_artifact_sha256")}, indent=2))
    if args.checkpoint_diagnostic:
        checkpoint_diagnostic(csv)


def checkpoint_diagnostic(csv: Path) -> None:
    """Corroborate target scale; this is NOT a generalization evaluation."""
    import torch
    from models.train_model import SolarDataset, CoroniumV3

    torch.set_num_threads(2)
    dataset = SolarDataset(str(csv.parent), str(csv))
    weights = ROOT / "models/best_coronium_v3_pro_augmented.pth"
    model = CoroniumV3(in_channels=2, dropout_rate=0.2)
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True))
    model.eval()
    samples = []
    with torch.no_grad():
        for index in np.linspace(0, len(dataset)-1, 16, dtype=int):
            x, y = dataset[int(index)]
            samples.append({"source_row": int(index), "target": y.item(),
                            "prediction": model(x[None]).item(),
                            "old_api_log_input_prediction": model(torch.log1p(x)[None]).item()})
    real = np.array([s["target"] for s in samples])
    pred = np.array([s["prediction"] for s in samples])
    old_pred = np.array([s["old_api_log_input_prediction"] for s in samples])
    scaler = json.loads((ROOT / "models/target_scaler.json").read_text())
    result = {
        "status": "target_interpretation_diagnostic_only_not_independent_validation",
        "weights_sha256": sha256(weights), "metadata_sha256": sha256(csv),
        "method": "16 evenly spaced source rows; CPU eval, no dropout; 2 threads",
        "samples": samples,
        "mae_against_candidate_representations": {
            "raw_SI": float(abs(pred-real).mean()),
            "natural_log_SI": float(abs(pred-np.log(real)).mean()),
            "log1p_SI": float(abs(pred-np.log1p(real)).mean()),
            "zscore_using_preserved_scaler": float(abs(pred-(real-scaler['mean'])/scaler['std']).mean()),
            "old_api_log_input_against_raw_SI": float(abs(old_pred-real).mean()),
        },
    }
    preserve_json(ROOT / "reports/phase1_v1/checkpoint_diagnostic.json", result)
    print(json.dumps(result["mae_against_candidate_representations"], indent=2))


if __name__ == "__main__":
    main()
