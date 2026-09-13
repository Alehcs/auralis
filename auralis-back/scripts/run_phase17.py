"""Audit-derived V3.1 metrics/figures from immutable Phase 1.5/1.6 artifacts.

Run from any directory: python scripts/run_phase17.py [--output-dir <fresh-dir>]
Repeat plots/data with recorded timing: --latency-from <previous-run>/latency.json
MC accuracy reuses the verified MPS T=20 CSV; CPU MC timing is a separate workload.
No training, artifact promotion, threshold fitting or changes to API inference.
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/auralis-phase17-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from models.active_model import CHECKPOINT_PATH, ONNX_PATH, MANIFEST_PATH, load_release
from models.train_model import CoroniumV3, enable_mc_dropout
from processing.model_input import prepare_model_input, processed_filename
from processing.scientific_split import load_split, sha256
from processing.observation_time import filename_time
from evaluate_final import compute_metrics
from plot_final_scatter import draw_scatter, save_figure, PROTOCOLS, COLORS, SCOPE
from plot_r2_diagnostic import draw_residual_histogram, draw_residual_scatter

BASE = ROOT / "reports/phase17_coronium_v3_1"
PHASE16 = ROOT / "reports/phase16_coronium_v3_1"
METADATA = ROOT / "data/processed/metadata_processed.csv"
SPLIT = ROOT / "models/split_indices_phase1_v1.json"
BANDS = ("low", "medium", "high")


def write_json(path, data):
    with Path(path).open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False, ensure_ascii=False)
        stream.write("\n")


def activity_bands(y):
    """Bands use the TARGET, fixed demo boundaries, never predicted GOES classes."""
    return np.where(np.asarray(y) < 1.41, "low", np.where(np.asarray(y) < 1.75, "medium", "high"))


def summarize(y, prediction):
    y, prediction = np.asarray(y, dtype=np.float64), np.asarray(prediction, dtype=np.float64)
    if y.shape != prediction.shape or y.ndim != 1 or not np.isfinite([y, prediction]).all():
        raise ValueError("Expected paired finite one-dimensional targets/predictions")
    if not len(y):
        return {"n": 0, **{k: None for k in ("mae", "rmse", "r2", "mape", "bias", "median_ae", "p90_ae", "p95_ae", "max_ae")}, "mape_nonzero_n": 0}
    residual, error = prediction-y, abs(prediction-y)
    result = compute_metrics(y, prediction)
    result = {k: v if np.isfinite(v) else None for k, v in result.items()}
    return {"n": len(y), **result, "mape_nonzero_n": int(np.count_nonzero(y)),
            "bias": float(residual.mean()), "median_ae": float(np.median(error)),
            "p90_ae": float(np.quantile(error, .9)), "p95_ae": float(np.quantile(error, .95)),
            "max_ae": float(error.max())}


def align_predictions(mc, det, metadata, split):
    """Refuse row-order mistakes, missing/duplicated observations and target drift."""
    expected = split["val"]
    for frame in (mc, det):
        if frame.source_row.tolist() != expected or not frame.processed_file.is_unique:
            raise ValueError("Prediction identities/order do not match clean validation")
        if frame.processed_file.tolist() != [processed_filename(metadata.iloc[i]) for i in expected]:
            raise ValueError("Prediction filenames do not match metadata")
        target = metadata.iloc[expected].sunspot_index.to_numpy(dtype=np.float32).astype(np.float64)
        if not np.array_equal(frame.target_si.to_numpy(), target):
            raise ValueError("Prediction targets do not match stored float32 SI contract")
    if set(processed_filename(metadata.iloc[i]) for i in split["train"]) & set(mc.processed_file):
        raise ValueError("Train/validation observation leakage")
    data = mc[["source_row", "processed_file", "target_si"]].copy()
    data["mc_si"] = mc.prediction_si
    data["onnx_si"] = det.onnx_si
    data["pytorch_si"] = det.pytorch_si
    data["activity_band_target"] = activity_bands(data.target_si)
    for key in PROTOCOLS:
        data[key + "_residual"] = data[key] - data.target_si
        data[key + "_absolute_error"] = abs(data[key] - data.target_si)
    return data


def load_sources():
    release = load_release()
    manifest = json.loads(MANIFEST_PATH.read_text())
    sources = {}
    for group in ("artifacts_sha256", "sources_sha256"):
        for name, expected in manifest[group].items():
            if sha256(ROOT / name) != expected:
                raise ValueError(f"Release source hash mismatch: {name}")
            sources[name] = expected
    run = ROOT / manifest["source_run"]
    metadata = pd.read_csv(METADATA)
    split = load_split(SPLIT, METADATA)
    mc = pd.read_csv(PHASE16 / "coronium_v3_1_mc_predictions.csv", float_precision="round_trip")
    det = pd.read_csv(PHASE16 / "coronium_v3_1_deterministic_predictions.csv", float_precision="round_trip")
    data = align_predictions(mc, det, metadata, split)
    history = json.loads((run / "history.json").read_text())
    if len({len(v) for v in history.values()}) != 1 or not np.isfinite(list(history.values())).all():
        raise ValueError("Invalid training history")
    if int(np.argmin(history["val_mae"])) + 1 != manifest["best_epoch"]:
        raise ValueError("Best epoch disagrees with selection history")
    evidence_path = ROOT / "reports/phase1_v1/evidence.json"
    evidence = json.loads(evidence_path.read_text())
    training = json.loads((run / "manifest.json").read_text())
    if sha256(evidence_path) != training["evidence_sha256"]:
        raise ValueError("Input evidence manifest changed")
    sources[str(evidence_path.relative_to(ROOT))] = sha256(evidence_path)
    # All 1,314 inputs, including training data used to define the baseline.
    for name, expected in evidence["npy_sha256"].items():
        path = ROOT / "data/processed" / name
        if sha256(path) != expected:
            raise ValueError(f"Input artifact changed: {name}")
    for path in (MANIFEST_PATH, ROOT / "experiments/results_benchmarking.json", ROOT / "experiments/exp_005_v3pro_augmented.json"):
        sources[str(path.relative_to(ROOT))] = sha256(path)
    return release, manifest, metadata, split, data, history, sources


def environment():
    def sysctl(name):
        try:
            return subprocess.check_output(["sysctl", "-n", name], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "processor": sysctl("machdep.cpu.brand_string"), "memory_bytes": sysctl("hw.memsize"),
            "logical_cpus": os.cpu_count(), "torch": torch.__version__, "onnxruntime": ort.__version__,
            "numpy": np.__version__, "pandas": pd.__version__, "matplotlib": matplotlib.__version__,
            "torch_threads": torch.get_num_threads(), "torch_interop_threads": torch.get_num_interop_threads(),
            "mps_available": torch.backends.mps.is_available()}


def measure_latency(data, runs=60, warmup=10):
    """CPU synchronous forward-only timing, real tensors, interleaved engine order."""
    if runs < 10 or warmup < 1:
        raise ValueError("Latency requires >=10 runs and >=1 warmup")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    session = ort.InferenceSession(str(ONNX_PATH), sess_options=options, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    models = {}
    for key in ("pytorch_eval_cpu", "pytorch_mc20_cpu"):
        model = CoroniumV3().cpu()
        model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=True))
        model.eval()
        if "mc20" in key:
            enable_mc_dropout(model)
        models[key] = model
    selected = data.sort_values("target_si").iloc[np.linspace(0, len(data)-1, 9).astype(int)]
    arrays = [prepare_model_input(np.load(ROOT / "data/processed" / f, allow_pickle=False))[None] for f in selected.processed_file]
    tensors = [torch.from_numpy(a) for a in arrays]
    def forward(key, i):
        if key == "onnx_eval_cpu":
            return float(session.run(None, {input_name: arrays[i]})[0].item())
        if key == "pytorch_eval_cpu":
            return float(models[key](tensors[i]).item())
        return float(torch.stack([models[key](tensors[i]) for _ in range(20)]).mean().item())
    keys = ("onnx_eval_cpu", "pytorch_eval_cpu", "pytorch_mc20_cpu")
    torch.manual_seed(42)
    records = []
    with torch.inference_mode():
        for key in keys:
            for i in range(warmup):
                forward(key, i % len(arrays))
        rng = np.random.default_rng(42)
        for repeat in range(runs):
            for order, key in enumerate(rng.permutation(keys)):
                i = repeat % len(arrays)
                start = time.perf_counter_ns()
                value = forward(key, i)
                elapsed = (time.perf_counter_ns() - start) / 1e6
                records.append({"repeat": repeat, "order": order, "protocol": str(key),
                                "source_row": int(selected.iloc[i].source_row), "latency_ms": elapsed,
                                "prediction_si": value})
            if (repeat + 1) % 10 == 0:
                print(f"Latency: {repeat+1}/{runs} rounds (3 workloads)", flush=True)
    result = {"model_name": "Coronium V3.1", "model_version": "3.1", "measured_utc": datetime.now(timezone.utc).isoformat(),
              "checkpoint_sha256": sha256(CHECKPOINT_PATH), "onnx_sha256": sha256(ONNX_PATH),
              "environment": environment(), "providers": session.get_providers(), "batch_size": 1,
              "shape": [1, 2, 512, 512], "dtype": "float32", "warmup_per_protocol": warmup,
              "runs_per_protocol": runs, "seed": 42, "ort_intra_threads": 4, "ort_inter_threads": 1,
              "ort_execution": "ORT_SEQUENTIAL", "ort_graph_optimization": "ORT_ENABLE_ALL (default)",
              "scope": "CPU synchronous forward + scalar extraction; inputs resident in memory; excludes loading, preprocessing, startup, HTTP, cache and API noise diagnostic",
              "mc_note": "CPU MC T=20 batch=1 timing workload only; accuracy report uses archived MPS batch=32 evaluation, not these timing outputs",
              "sample_selection": "9 evenly spaced target order statistics; protocol order shuffled per round seed=42",
              "samples": selected[["source_row", "processed_file", "target_si"]].to_dict("records"),
              "raw_measurements": records, "summary": {}}
    for key in keys:
        values = np.array([r["latency_ms"] for r in records if r["protocol"] == key])
        result["summary"][key] = {"n": len(values), "mean_ms": float(values.mean()),
            "std_ms": float(values.std(ddof=1)), "median_ms": float(np.median(values)),
            "p90_ms": float(np.quantile(values, .9)), "p95_ms": float(np.quantile(values, .95)),
            "min_ms": float(values.min()), "max_ms": float(values.max())}
    return result


def build_tables(release, metadata, split, data):
    # Reuse the existing constant-mean baseline's estimator without loading 1,051 images.
    from src.experiments.run_external_baselines import NaivePersistence
    baseline = NaivePersistence()
    labels = torch.tensor(metadata.iloc[split["train"]].sunspot_index.to_numpy(dtype=np.float32)).reshape(-1, 1)
    baseline.fit([(None, labels)])
    data["train_mean_si"] = baseline.mean
    metrics, bands, worst = {}, [], []
    for key in (*PROTOCOLS, "pytorch_si", "train_mean_si"):
        metrics[key] = summarize(data.target_si, data[key])
        if key in PROTOCOLS:
            for band in BANDS:
                rows = data[data.activity_band_target == band]
                bands.append({"protocol": key, "band": band, **summarize(rows.target_si, rows[key])})
            top = data.sort_values(key + "_absolute_error", ascending=False, kind="stable").head(10)
            for rank, (_, row) in enumerate(top.iterrows(), 1):
                timing = filename_time(row.processed_file)
                worst.append({"protocol": key, "rank": rank, **row.to_dict(),
                              "record_time_tai": timing["date_original"], "record_time_utc": timing["date_utc"],
                              "csv_date_original": str(metadata.iloc[int(row.source_row)].date), "csv_date_scale": "unknown"})
    for key, reference in (("mc_si", release["official_mc_dropout"]["metrics"]),
                           ("onnx_si", release["serving_deterministic"]["onnx"]),
                           ("pytorch_si", release["serving_deterministic"]["pytorch"])):
        for metric in ("mae", "rmse", "r2", "mape"):
            np.testing.assert_allclose(metrics[key][metric], reference[metric], atol=2e-6, rtol=1e-6)
    delta_error = data.onnx_si_absolute_error - data.mc_si_absolute_error
    comparison = {"same_observations": len(data), "deterministic_minus_mc_mae": float(delta_error.mean()),
                  "mc_lower_absolute_error_n": int((delta_error > 0).sum()),
                  "deterministic_lower_absolute_error_n": int((delta_error < 0).sum()),
                  "ties_n": int((delta_error == 0).sum()),
                  "mean_mc_minus_deterministic_prediction_si_pp": float((data.mc_si-data.onnx_si).mean()),
                  "max_abs_pytorch_onnx_difference": float(abs(data.pytorch_si-data.onnx_si).max()),
                  "claim_scope": SCOPE + "; one selected checkpoint and one seeded MC evaluation, no general superiority claim"}
    return metrics, pd.DataFrame(bands), pd.DataFrame(worst), comparison, baseline.mean


def plot_all(out, data, history, best_epoch, bands, worst, metrics, latency):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 10,
                         "axes.spines.top": False, "axes.spines.right": False, "svg.hashsalt": "auralis-phase17-v1"})
    figures = out / "figures"
    def finish(fig, stem, title, scope=SCOPE):
        fig.suptitle(f"Coronium V3.1 · {title}\n{scope}", fontsize=12)
        save_figure(fig, figures / stem)
    y = data.target_si.to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), layout="constrained")
    for ax, (key, label) in zip(axes, PROTOCOLS.items()):
        draw_scatter(ax, y, data[key].to_numpy(), label, COLORS[key])
    finish(fig, "01_target_prediction", "Target versus prediction")

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained", sharey=True)
    for row, (key, label) in zip(axes, PROTOCOLS.items()):
        residual = data[key].to_numpy()-y
        draw_residual_scatter(row[0], data[key], residual, "Predicted SI (%)", label, COLORS[key])
        draw_residual_scatter(row[1], y, residual, "Target SI (%)", label, COLORS[key])
    finish(fig, "02_residuals", "Residuals versus prediction and target")

    residuals = {key: data[key].to_numpy()-y for key in PROTOCOLS}
    bins = np.histogram_bin_edges(np.concatenate(list(residuals.values())), bins="fd")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained", sharex=True, sharey=True)
    for ax, (key, label) in zip(axes, PROTOCOLS.items()):
        draw_residual_histogram(ax, residuals[key], bins, label, COLORS[key])
    finish(fig, "03_residual_distribution", "Residual distribution (common bins)")

    bins = np.histogram_bin_edges(np.concatenate([abs(v) for v in residuals.values()]), bins="fd")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained", sharex=True, sharey=True)
    for ax, (key, label) in zip(axes, PROTOCOLS.items()):
        ax.hist(abs(residuals[key]), bins=bins, color=COLORS[key], edgecolor="white")
        ax.set(xlabel="Absolute error (SI pp)", ylabel="Observations", title=label)
        ax.grid(alpha=.2, axis="y")
    finish(fig, "04_absolute_error_distribution", "Absolute error distribution (common bins)")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    for ax, metric, unit in zip(axes, ("mae", "bias"), ("MAE (SI pp)", "Mean residual (SI pp)")):
        for j, (key, label) in enumerate(PROTOCOLS.items()):
            values = bands[bands.protocol == key].set_index("band").reindex(BANDS)
            ax.bar(np.arange(3)+(j-.5)*.35, values[metric], width=.35, color=COLORS[key], label=label)
        counts = [int((data.activity_band_target == b).sum()) for b in BANDS]
        ax.set_xticks(np.arange(3), [f"{b.title()}\nn={n}" for b, n in zip(BANDS, counts)])
        ax.set(ylabel=unit, xlabel="Target-based activity band (internal demo thresholds)")
        ax.axhline(0, color="black", lw=.8)
        ax.legend(fontsize=7)
    finish(fig, "05_activity_band_errors", "Errors by activity · low <1.41; medium <1.75; high ≥1.75 SI %")

    # Publication reconstruction of frozen trainer history with correct protocol and units.
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), layout="constrained", sharex=True)
    epochs = np.arange(1, len(history["val_mae"])+1)
    for ax, train, val, unit in ((axes[0], "train_whl", "val_whl", "Weighted Huber objective (SI pp²)"),
                                (axes[1], "train_mae", "val_mae", "MAE (SI pp)")):
        ax.plot(epochs, history[train], label="Train · augmentation + dropout + BatchNorm train", color="#009E73")
        ax.plot(epochs, history[val], label="Validation · MC T=20 · BatchNorm eval", color=COLORS["mc_si"])
        ax.set_ylabel(unit)
        ax.set_yscale("log")
        ax.legend(fontsize=8)
    axes[2].step(epochs, history["learning_rate"], where="post", color="#CC79A7")
    axes[2].set(yscale="log", ylabel="AdamW learning rate", xlabel="Epoch")
    for ax in axes:
        ax.axvline(best_epoch, color="black", ls="--", label=f"Selected epoch {best_epoch}")
        ax.grid(alpha=.2)
    finish(fig, "06_training_validation", f"Training and validation · selected epoch {best_epoch} of {len(epochs)}",
           "Phase 1.5 weights promoted as V3.1 · log axes; raw SI targets · train/validation protocols differ")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    axes[0].scatter(data.onnx_si, data.mc_si, color=COLORS["mc_si"], s=20)
    lo, hi = min(data.onnx_si.min(), data.mc_si.min()), max(data.onnx_si.max(), data.mc_si.max())
    axes[0].plot([lo, hi], [lo, hi], "k--", lw=1)
    axes[0].set(xlabel="Deterministic ONNX SI (%)", ylabel="MC T=20 SI (%)", title="Paired predictions")
    axes[0].set_aspect("equal", adjustable="box")
    axes[1].scatter(y, data.onnx_si_absolute_error-data.mc_si_absolute_error, s=18, color="#009E73")
    axes[1].axhline(0, color="black", ls="--")
    axes[1].set(xlabel="Target SI (%)", ylabel="|Deterministic error| − |MC error| (SI pp)",
                title="Positive: MC smaller error; negative: deterministic smaller")
    finish(fig, "07_protocol_difference", "MC T=20 (MPS) versus deterministic ONNX (CPU)")

    fig, axes = plt.subplots(1, 4, figsize=(14, 5), layout="constrained")
    keys = ["train_mean_si", "mc_si", "onnx_si"]
    labels = ["Train\nmean", "V3.1\nMC T=20", "V3.1\nONNX eval"]
    for ax, metric, unit in zip(axes, ("mae", "rmse", "r2", "mape"), ("MAE (SI pp)", "RMSE (SI pp)", "R² (dimensionless)", "MAPE (%)")):
        bars = ax.bar(labels, [metrics[k][metric] for k in keys], color=["#777777", COLORS["mc_si"], COLORS["onnx_si"]])
        ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
        ax.margins(y=.18)
        ax.set_ylabel(unit)
        ax.axhline(0, color="black", lw=.8)
    finish(fig, "08_clean_baseline", "Constant training-mean baseline on the same 263 observations")

    fig, axes = plt.subplots(2, 3, figsize=(12, 8), layout="constrained")
    for row_axes, (key, label) in zip(axes, PROTOCOLS.items()):
        for ax, (_, row) in zip(row_axes, worst[worst.protocol == key].head(3).iterrows()):
            raw = np.load(ROOT / "data/processed" / row.processed_file, allow_pickle=False)
            ax.imshow(raw, cmap="gray", vmin=-1, vmax=1, origin="lower")
            ax.set_xticks([0, 256, 511]); ax.set_yticks([0, 256, 511])
            ax.set(xlabel="Column (resized pixel)", ylabel="Row (resized pixel)",
                title=f"{key.replace('_si','').upper()} · rank {row['rank']} · row {row.source_row}\n"
                      f"{row.record_time_tai[:10]} TAI · target {row.target_si:.3f}%\n"
                      f"pred {row[key]:.3f}% · residual {row[key+'_residual']:+.3f} SI pp")
    finish(fig, "09_largest_error_cases", "Three largest errors per protocol · ranked on validation",
           "MC T=20 MPS / deterministic ONNX CPU · grayscale = clip(resize(B_LOS), ±400 G) / 400 in [−1,1]")

    # TAI calendar years, explicitly descriptive for this random split, never a temporal test.
    data_year = data.processed_file.str.extract(r'hmi\.m_45s\.(\d{4})')[0].astype(int)
    years = sorted(data_year.unique())
    yearly = []
    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    for key, label in PROTOCOLS.items():
        values = []
        for year in years:
            rows = data[data_year == year]
            result = summarize(rows.target_si, rows[key]); values.append(result["mae"])
            yearly.append({"year_tai": int(year), "protocol": key, **result})
        ax.plot(years, values, marker="o", label=label, color=COLORS[key])
    ax.set_xticks(years, [f"{year}\nn={int((data_year==year).sum())}" for year in years])
    ax.set(xlabel="Filename record year (TAI)", ylabel="MAE (SI pp)")
    ax.legend(fontsize=8); ax.grid(alpha=.2)
    finish(fig, "10_error_by_record_year", "Descriptive error by record year · random selection validation")
    pd.DataFrame(yearly).to_csv(out / "metrics_by_record_year.csv", index=False, float_format="%.17g")

    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    names = list(latency["summary"])
    samples = [[r["latency_ms"] for r in latency["raw_measurements"] if r["protocol"] == key] for key in names]
    ax.boxplot(samples, tick_labels=["ONNX eval\nCPU · T=1", "PyTorch eval\nCPU · T=1", "PyTorch MC\nCPU · T=20"], showfliers=True)
    ax.set(ylabel="Forward + scalar extraction latency (ms; log axis)", yscale="log")
    ax.grid(alpha=.2, axis="y")
    finish(fig, "11_latency", f"Measured latency · batch 1 · 4 intra-op threads · n={latency['runs_per_protocol']} each",
           "Real inputs resident in memory; warm starts; excludes preprocessing and HTTP · CPU MC is a timing workload")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--latency-from", type=Path)
    parser.add_argument("--latency-runs", type=int, default=60)
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    out = args.output_dir or BASE / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = out.resolve()
    if out.exists():
        raise FileExistsError(out)
    release, manifest, metadata, split, data, history, sources = load_sources()
    print("Verified release hashes, all inputs, identities, clean split and history", flush=True)
    metrics, bands, worst, comparison, mean = build_tables(release, metadata, split, data)
    out.mkdir(parents=True, exist_ok=False)
    if args.latency_from:
        latency = json.loads(args.latency_from.read_text())
        if latency["checkpoint_sha256"] != sha256(CHECKPOINT_PATH) or latency["onnx_sha256"] != sha256(ONNX_PATH):
            raise ValueError("Timing artifacts do not match V3.1")
        prior_manifest = json.loads((args.latency_from.parent / "manifest.json").read_text())
        if sha256(args.latency_from) != prior_manifest["outputs_sha256"]["latency.json"]:
            raise ValueError("Timing source hash mismatch")
        latency_origin = {"mode": "reused_measurement", "path": str(args.latency_from.resolve()), "sha256": sha256(args.latency_from)}
    else:
        latency = measure_latency(data, args.latency_runs, args.warmup)
        latency_origin = {"mode": "measured_this_run"}
    write_json(out / "latency.json", latency)
    pd.DataFrame(latency["raw_measurements"]).to_csv(out / "latency_samples.csv", index=False, float_format="%.17g")
    data.to_csv(out / "predictions.csv", index=False, float_format="%.17g")
    bands.to_csv(out / "metrics_by_activity.csv", index=False, float_format="%.17g")
    worst.to_csv(out / "worst_cases.csv", index=False, float_format="%.17g")
    pd.DataFrame({"epoch": np.arange(1, len(history["val_mae"])+1), **history}).to_csv(out / "training_history.csv", index=False, float_format="%.17g")
    model = CoroniumV3()
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=True))
    artifacts = {"parameters": sum(p.numel() for p in model.parameters()),
                 "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
                 "files": {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size, "MiB": p.stat().st_size / 2**20, "sha256": sha256(p)} for p in (CHECKPOINT_PATH, ONNX_PATH)},
                 "onnx_external_data": manifest["onnx_export"]["external_data"]}
    if artifacts["parameters"] != manifest["parameters"]:
        raise ValueError("Model parameter count mismatch")
    results = {"model_name": "Coronium V3.1", "model_version": "3.1", "scope": SCOPE,
               "units": "SI percent targets/predictions; SI percentage points errors; dimensionless R2; MAPE percent excluding zero targets",
               "arithmetic": "float64 recomputation of archived float32 predictions; release MC float32 reductions can differ in last decimals",
               "residual_definition": "prediction minus target", "protocols": PROTOCOLS,
               "metrics": metrics, "paired_comparison": comparison,
               "activity_bands": {"based_on": "target", "low": "SI < 1.41", "medium": "1.41 <= SI < 1.75", "high": "SI >= 1.75", "scope": "internal demo bands, no GOES/calibration claim"},
               "constant_baseline": {"name": "Training mean (existing NaivePersistence estimator; not temporal persistence)", "mean_si": mean, "fit_observations": len(split["train"]), "validation_observations": len(data)},
               "training": {"best_epoch": manifest["best_epoch"], "epochs": len(history["val_mae"]), "best_training_loop_val_mae": min(history["val_mae"]), "note": "Training RNG stream differs from standalone seeded MC reevaluation"},
               "artifacts": artifacts, "historical_v3": release["historical_v3"],
               "historical_comparison": "V3: 353 rows, 145 overlapping observations; V3.1: 263 unique selection-validation observations, 0 overlap. Different weights/splits/protocols: descriptive table only, no improvement estimate.",
               "external_baselines": {"source": "experiments/results_benchmarking.json", "status": "historical_only_not_comparable_to_v31", "reason": "352-row validation versus 263; original split/checkpoint/input provenance unavailable for a matched clean evaluation"}}
    write_json(out / "metrics.json", results)
    metric_rows = [{"model": "Coronium V3.1" if k != "train_mean_si" else "Training mean", "protocol": k, **v} for k, v in metrics.items()]
    pd.DataFrame(metric_rows).to_csv(out / "metrics.csv", index=False, float_format="%.17g")
    historic = [{"model": "Coronium V3 historical", "protocol": "historical MC T=20", "n": 353, "overlap": 145, **release["historical_v3"]["metrics"]}]
    historic.extend({"model": "Coronium V3.1", "protocol": key, "n": len(data), "overlap": 0, **{m: metrics[key][m] for m in ("mae", "rmse", "r2", "mape")}} for key in PROTOCOLS)
    pd.DataFrame(historic).to_csv(out / "historical_protocol_comparison.csv", index=False, float_format="%.17g")
    plot_all(out, data, history, manifest["best_epoch"], bands, worst, metrics, latency)
    subprocess.run([sys.executable, str(ROOT / "scripts/plot_architecture_diagram.py"),
                    "--output", str(out / "figures/12_architecture.png")], cwd=ROOT, check=True)
    selected_case = worst[worst.protocol == "onnx_si"].iloc[0].processed_file
    subprocess.run([sys.executable, str(ROOT / "scripts/plot_gradcam_overlay.py"),
                    "--sample", selected_case, "--output", str(out / "figures/13_gradcam_largest_deterministic_error.png")],
                   cwd=ROOT, check=True)
    write_json(out / "environment.json", environment())
    # Copy exact scripts plus shared source dependencies; manifest hashes inputs and outputs.
    source_paths = [Path(__file__), ROOT / "scripts/plot_final_scatter.py", ROOT / "scripts/plot_r2_diagnostic.py", ROOT / "scripts/evaluate_final.py", ROOT / "src/experiments/run_external_baselines.py", ROOT / "scripts/plot_architecture_diagram.py", ROOT / "scripts/plot_gradcam_overlay.py", ROOT / "src/processing/observation_time.py", ROOT / "src/processing/scientific_split.py", ROOT / "src/models/active_model.py"]
    source_paths += [ROOT / name for name in sources if name.endswith('.py')]
    for path in set(source_paths):
        relative = path.relative_to(ROOT)
        destination = out / "sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        sources[str(relative)] = sha256(path)
    catalog = [{"name": p.stem, "formats": ["png", "pdf", "svg"]} for p in sorted((out / "figures").glob("*.png"))]
    write_json(out / "figure_catalog.json", catalog)
    report = ["# Coronium V3.1 — Fase 1.7", "", SCOPE, "", "| Protocolo | N | MAE (SI pp) | RMSE (SI pp) | R² | MAPE (%) |", "|---|---:|---:|---:|---:|---:|"]
    for row in metric_rows:
        report.append(f"| {row['protocol']} | {row['n']} | {row['mae']:.8f} | {row['rmse']:.8f} | {row['r2']:.8f} | {row['mape']:.8f} |")
    report += ["", "Los CSV contienen casos individuales, errores por banda y año TAI; métricas JSON incluye sesgo y percentiles.", "", "Las figuras incluyen modelo, protocolo y alcance; pp = puntos porcentuales de SI.", "", "## Figuras", ""]
    for item in catalog:
        name = item["name"]
        report += [f"### {name}", "", f"![{name}](figures/{name}.png)", "", f"[PDF vectorial](figures/{name}.pdf) · [SVG](figures/{name}.svg)", ""]
    (out / "report.md").write_text("\n".join(report))
    output_hashes = {str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob('*')) if p.is_file()}
    write_json(out / "manifest.json", {"schema": "auralis-phase17-v1", "status": "completed", "model_version": "3.1", "created_utc": datetime.now(timezone.utc).isoformat(),
               "command": sys.argv, "cwd": str(Path.cwd()), "source_run": manifest["source_run"], "sources_sha256": sources, "outputs_sha256": output_hashes,
               "latency_origin": latency_origin, "verification": {"release_hashes": "passed", "all_input_hashes": "passed", "row_identity_and_target_contract": "passed", "observation_overlap": 0, "official_metric_parity": "passed"}})
    print(json.dumps({"output": str(out), "metrics": metrics, "paired_comparison": comparison, "artifacts": artifacts, "latency": latency["summary"], "figures": len(catalog)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
