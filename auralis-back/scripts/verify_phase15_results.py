"""Verify a completed Phase 1.5 run and two independently executed evaluations."""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from processing.model_input import processed_filename
from processing.scientific_split import load_split, sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--repeat", type=Path, required=True)
    args = parser.parse_args()
    csv = ROOT / "data/processed/metadata_processed.csv"
    split = load_split(ROOT / "models/split_indices_phase1_v1.json", csv)
    training = json.loads((args.run_dir / "manifest.json").read_text())
    evaluated = json.loads((args.evaluation / "manifest.json").read_text())
    repeated = json.loads((args.repeat / "manifest.json").read_text())
    first = pd.read_csv(args.evaluation / "predictions.csv", float_precision="round_trip")
    second = pd.read_csv(args.repeat / "predictions.csv", float_precision="round_trip")
    if training["status"] != "completed_unpromoted" or not evaluated.get("evaluation_completed") or not repeated.get("evaluation_completed"):
        raise ValueError("Run/evaluations are not complete")
    weight_hash = sha256(args.run_dir / "best.pth")
    if any(m["weights_sha256"] != weight_hash for m in (evaluated, repeated)):
        raise ValueError("Evaluations use different weights")
    if training["checkpoint_sha256"] != weight_hash:
        raise ValueError("Trained checkpoint was changed")
    selected = args.run_dir / "epochs" / f"best_epoch_{training['best_epoch']:04d}.pth"
    # torch.save includes the archive name; compare tensor content separately.
    import torch
    best = torch.load(args.run_dir / "best.pth", map_location="cpu", weights_only=True)
    archived = torch.load(selected, map_location="cpu", weights_only=True)
    if best.keys() != archived.keys() or any(not torch.equal(best[k], archived[k]) for k in best):
        raise ValueError("Final best.pth differs from its selected epoch")
    if training.get("initialization") != "random_from_scratch_no_pretrained_weights":
        raise ValueError("Training provenance does not establish fresh initialization")
    if training["initial_checkpoint_sha256"] != sha256(args.run_dir / "initial.pth"):
        raise ValueError("Initial state was changed")
    history = json.loads((args.run_dir / "history.json").read_text())
    if training["best_epoch"] != int(np.argmin(history["val_mae"])) + 1:
        raise ValueError("Checkpoint is not the predeclared minimum-validation-MAE epoch")
    if first["source_row"].tolist() != split["val"] or len(first) != 263:
        raise ValueError("Predictions do not cover the exact clean validation observations")
    metadata = pd.read_csv(csv)
    expected_names = [processed_filename(metadata.iloc[i]) for i in split["val"]]
    if first.processed_file.tolist() != expected_names:
        raise ValueError("Prediction identities do not match the split")
    expected_y = metadata.sunspot_index.iloc[split["val"]].to_numpy(dtype=np.float32)
    np.testing.assert_array_equal(first.target_si.to_numpy(), expected_y)
    pd.testing.assert_frame_equal(first, second, check_exact=True)
    if evaluated["metrics"] != repeated["metrics"]:
        raise ValueError("Repeated evaluation metrics are not identical")
    y, pred = first.target_si.to_numpy(), first.prediction_si.to_numpy()
    if not np.isfinite(y).all() or not np.isfinite(pred).all():
        raise ValueError("Non-finite evaluation outputs")
    nonzero = y != 0
    metrics = {
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "r2": float(r2_score(y, pred)),
        "mape": float(np.mean(abs((pred[nonzero]-y[nonzero])/y[nonzero]))*100),
    }
    for name, value in metrics.items():
        if not np.isclose(value, evaluated["metrics"][name], atol=2e-6, rtol=1e-6):
            raise ValueError(f"Independent metric check failed: {name}")
    # Reference baseline uses ONLY the training targets, with no fitted image model.
    train_mean = float(metadata.sunspot_index.iloc[split["train"]].mean())
    constant = np.full_like(y, train_mean)
    result = {
        "status": "verified", "validation_observations": len(first), "observation_overlap": 0,
        "same_predictions_in_two_processes": True, "identical_repeated_metrics": True,
        "checkpoint_sha256": weight_hash, "best_epoch": training["best_epoch"],
        "metrics_recomputed_float64_sklearn": metrics,
        "reported_metrics": evaluated["metrics"], "mape_nonzero_samples": int(nonzero.sum()),
        "constant_training_mean_reference": {"training_mean": train_mean,
            "mae": float(mean_absolute_error(y, constant)),
            "rmse": float(np.sqrt(mean_squared_error(y, constant))),
            "r2": float(r2_score(y, constant))},
        "scope": "clean observation validation used for model selection; not an independent test or temporal validation",
    }
    with (args.run_dir / "verification.json").open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
