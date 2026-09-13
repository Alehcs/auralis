"""Reproducible Phase 1.5 entrypoint; fresh training or evaluation of its run.

Uses the Phase 1 dataset, architecture, augmentations, loss, optimizer and split.
No legacy weights are loaded for training. A fresh directory is mandatory.
"""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from models import train_model
from processing.scientific_split import load_split, sha256


def configure_reproducibility() -> None:
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
        torch.backends.cudnn.benchmark = False


def verify_artifacts() -> dict:
    evidence = json.loads((ROOT / "reports/phase1_v1/evidence.json").read_text())
    for name, expected in evidence["preserved_artifact_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Historical artifact changed: {name}")
    for name, expected in evidence["npy_sha256"].items():
        if sha256(ROOT / "data/processed" / name) != expected:
            raise ValueError(f"Input changed: {name}")
    split = load_split(ROOT / "models/split_indices_phase1_v1.json",
                      ROOT / "data/processed/metadata_processed.csv")
    return {"historical_artifacts_preserved": True, "npy_hashes_verified": len(evidence["npy_sha256"]),
            "train_observations": len(split["train"]), "validation_observations": len(split["val"]),
            "observation_overlap": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--train-run", type=Path)
    mode.add_argument("--evaluate-run", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    configure_reproducibility()
    checks = verify_artifacts()
    print(json.dumps(checks), flush=True)
    if args.evaluate_run:
        if args.output_dir is None:
            parser.error("Evaluation requires a fresh --output-dir")
        import evaluate_final
        configure_reproducibility()
        sys.argv = ["evaluate_final.py", "--run-dir", str(args.evaluate_run),
                    "--output-dir", str(args.output_dir)]
        evaluate_final.main()
        return

    sources = [ROOT / "src/models/train_model.py", ROOT / "src/processing/model_input.py",
               ROOT / "src/processing/scientific_split.py", ROOT / "scripts/evaluate_final.py",
               Path(__file__).resolve()]
    snapshots = {str(p.relative_to(ROOT)): p.read_text() for p in sources}
    environment = {
        "python": sys.version, "platform": platform.platform(),
        "machine": platform.machine(), "python_executable": sys.executable,
        "seed": 42, "torch_threads": 4, "deterministic_algorithms": True,
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "mps_high_watermark_ratio": os.environ.get("PYTORCH_MPS_HIGH_WATERMARK_RATIO"),
        "mps_low_watermark_ratio": os.environ.get("PYTORCH_MPS_LOW_WATERMARK_RATIO"),
        "mps_available": torch.backends.mps.is_available(),
        "versions": {name: importlib.metadata.version(name) for name in
                     ("torch", "torchvision", "numpy", "pandas", "scikit-learn")},
    }
    try:
        train_model.main(args.train_run)
    except Exception as exc:
        if args.train_run.exists():
            with (args.train_run / "failure.json").open("x") as stream:
                json.dump({"status": "failed_do_not_evaluate", "error": repr(exc),
                           "environment": environment}, stream, indent=2)
        raise
    for name, source in snapshots.items():
        if (ROOT / name).read_text() != source:
            raise RuntimeError(f"Scientific source changed during training: {name}")
        path = args.train_run / "sources" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(source)
    with (args.train_run / "environment.json").open("x") as stream:
        json.dump(environment, stream, indent=2)
    with (args.train_run / "artifact_verification.json").open("x") as stream:
        json.dump({"before": checks, "after": verify_artifacts()}, stream, indent=2)
    print(f"TRAINING_COMPLETE run_dir={args.train_run}", flush=True)


if __name__ == "__main__":
    main()
