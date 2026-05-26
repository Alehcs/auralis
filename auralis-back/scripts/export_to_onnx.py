"""Export CoroniumV3 PRO to ONNX and compare PyTorch/ORT latency.

The exported graph keeps a dynamic batch axis but preserves the production
input contract: ``(N, 2, 512, 512)`` dual-polarity magnetograms.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Make src/ importable
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent  # auralis-back/
sys.path.insert(0, str(ROOT / "src"))

from models.train_model import CoroniumV3              # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("auralis.export_onnx")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WEIGHTS_PATH = ROOT / "models" / "best_coronium_v3_pro_augmented.pth"
ONNX_PATH    = ROOT / "models" / "best_coronium_v3_pro.onnx"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INPUT_SHAPE   = (1, 2, 512, 512)   # (batch, B+/B-, H, W)
WARMUP_ITERS  = 10
BENCH_ITERS   = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_pytorch_model(weights_path: Path) -> CoroniumV3:
    """Instantiate CoroniumV3 PRO and load checkpoint weights."""
    model = CoroniumV3(in_channels=2, dropout_rate=0.2)
    state = torch.load(weights_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    logger.info("Weights loaded from: %s", weights_path.name)
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("Total parameters: %s", f"{n_params:,}")
    return model


def export_onnx(model: CoroniumV3, onnx_path: Path) -> None:
    """Trace and export the model graph to ONNX opset 17."""
    dummy_input = torch.zeros(*INPUT_SHAPE)

    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        opset_version=18,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input":  {0: "batch_size"},
            "output": {0: "batch_size"},
        },
        do_constant_folding=True,   # fuse constant sub-graphs for speed
    )
    size_kb = onnx_path.stat().st_size / 1024
    size_label = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
    logger.info("ONNX model saved: %s  (%s)", onnx_path.name, size_label)


def verify_onnx(onnx_path: Path) -> None:
    """Run onnx.checker to confirm the graph is valid before benchmarking."""
    try:
        import onnx  # type: ignore
        model_proto = onnx.load(str(onnx_path))
        onnx.checker.check_model(model_proto)
        logger.info("onnx.checker: graph is valid")
    except ImportError:
        logger.warning("onnx is not installed; skipping graph validation")


def benchmark_pytorch(model: CoroniumV3) -> Tuple[float, float]:
    """Return (mean_ms, std_ms) for BENCH_ITERS single-image forward passes."""
    dummy = torch.zeros(*INPUT_SHAPE)

    with torch.no_grad():
        # warm-up
        for _ in range(WARMUP_ITERS):
            _ = model(dummy)

        # measure
        times: list = []
        for _ in range(BENCH_ITERS):
            t0 = time.perf_counter()
            _ = model(dummy)
            times.append((time.perf_counter() - t0) * 1000)

    return float(np.mean(times)), float(np.std(times))


def benchmark_onnx(onnx_path: Path) -> Tuple[float, float]:
    """Return (mean_ms, std_ms) for BENCH_ITERS single-image ORT inferences."""
    try:
        import onnxruntime as ort  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "onnxruntime is not installed. Run: pip install onnxruntime"
        ) from exc

    sess_opts = ort.SessionOptions()
    sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(
        str(onnx_path),
        sess_options=sess_opts,
        providers=["CPUExecutionProvider"],
    )
    input_name = session.get_inputs()[0].name
    dummy_np   = np.zeros(INPUT_SHAPE, dtype=np.float32)

    # warm-up
    for _ in range(WARMUP_ITERS):
        _ = session.run(None, {input_name: dummy_np})

    # measure
    times: list = []
    for _ in range(BENCH_ITERS):
        t0 = time.perf_counter()
        _ = session.run(None, {input_name: dummy_np})
        times.append((time.perf_counter() - t0) * 1000)

    return float(np.mean(times)), float(np.std(times))


def print_report(
    onnx_path: Path,
    pt_mean: float,
    pt_std: float,
    ort_mean: float,
    ort_std: float,
) -> None:
    """Pretty-print a benchmark summary table."""
    size_kb    = onnx_path.stat().st_size / 1024
    size_label = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
    speedup    = pt_mean / ort_mean if ort_mean > 0 else float("inf")
    pct        = (pt_mean - ort_mean) / pt_mean * 100

    bar = "=" * 62
    print()
    print(bar)
    print("  CORONIUM V3 PRO — ONNX EXPORT & LATENCY BENCHMARK")
    print(bar)
    print(f"  Checkpoint  : {WEIGHTS_PATH.name}")
    print(f"  ONNX file   : {ONNX_PATH.name}  ({size_label})")
    print(f"  Input shape : {list(INPUT_SHAPE)}")
    print(f"  Warm-up     : {WARMUP_ITERS} iter   |   Bench: {BENCH_ITERS} iter")
    print("-" * 62)
    print(f"  {'Backend':<22}  {'Mean (ms)':>10}  {'Std (ms)':>10}")
    print(f"  {'-'*22}  {'-'*10}  {'-'*10}")
    print(f"  {'PyTorch (CPU)':<22}  {pt_mean:>10.2f}  {pt_std:>10.2f}")
    print(f"  {'ONNX Runtime (CPU)':<22}  {ort_mean:>10.2f}  {ort_std:>10.2f}")
    print("-" * 62)
    status = "faster" if speedup >= 1.0 else "slower"
    print(f"  Speedup ONNX vs PyTorch : {speedup:.2f}x  ({pct:+.1f}%)  {status}")
    print(bar)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Sanity check
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {WEIGHTS_PATH}\n"
            "Train the augmented model before exporting it."
        )

    # 2. Load PyTorch model.
    logger.info("Step 1/4 - Loading CoroniumV3 PRO architecture...")
    model = load_pytorch_model(WEIGHTS_PATH)

    # 3. Export to ONNX.
    logger.info("Step 2/4 - Exporting to ONNX (opset 18)...")
    export_onnx(model, ONNX_PATH)

    # 4. Validate graph.
    logger.info("Step 3/4 - Validating ONNX graph...")
    verify_onnx(ONNX_PATH)

    # 5. Benchmark.
    logger.info("Step 4/4 - Measuring latency (%d iterations, warm-up %d)...",
                BENCH_ITERS, WARMUP_ITERS)

    logger.info("  Benchmarking PyTorch...")
    pt_mean, pt_std = benchmark_pytorch(model)

    logger.info("  Benchmarking ONNX Runtime...")
    ort_mean, ort_std = benchmark_onnx(ONNX_PATH)

    # 6. Final report.
    print_report(ONNX_PATH, pt_mean, pt_std, ort_mean, ort_std)


if __name__ == "__main__":
    main()
