"""Publication scatter helpers and export from a verified Phase 1.7 report.

python scripts/plot_final_scatter.py --report-dir <phase17-run> --output-dir <fresh-dir>
Historical reports/results_comparison.csv is preserved and never the default.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from evaluate_final import compute_metrics

PROTOCOLS = {"mc_si": "MC Dropout T=20 · MPS · batch 32 · seed 42",
             "onnx_si": "Deterministic ONNX · CPU · batch 1"}
COLORS = {"mc_si": "#0072B2", "onnx_si": "#D55E00"}
SCOPE = "Selection validation; no untouched test or temporal generalization"


def save_figure(fig, stem):
    """Keep raster and vector exports together; never replace prior figures."""
    stem = Path(stem)
    for extension in ("png", "pdf", "svg"):
        if stem.with_suffix('.' + extension).exists():
            raise FileExistsError(stem.with_suffix('.' + extension))
    stem.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf", "svg"):
        metadata = {"Date": None} if extension == "svg" else (
            {"CreationDate": None, "ModDate": None} if extension == "pdf" else {})
        fig.savefig(stem.with_suffix('.' + extension), dpi=300, bbox_inches="tight", metadata=metadata)
    plt.close(fig)


def load_report(path):
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest.get("model_version") != "3.1" or manifest.get("status") != "completed":
        raise ValueError("A completed Coronium V3.1 Phase 1.7 report is required")
    csv = path / "predictions.csv"
    if hashlib.sha256(csv.read_bytes()).hexdigest() != manifest["outputs_sha256"]["predictions.csv"]:
        raise ValueError("Report predictions hash mismatch")
    return pd.read_csv(csv, float_precision="round_trip")


def draw_scatter(ax, y, prediction, label, color):
    metrics = compute_metrics(y, prediction)
    lo, hi = min(y.min(), prediction.min()), max(y.max(), prediction.max())
    pad = max((hi - lo) * .05, .01)
    ax.scatter(y, prediction, s=17, alpha=.65, color=color, edgecolors="none")
    ax.plot([lo-pad, hi+pad], [lo-pad, hi+pad], "--", color="#333333", lw=1, label="Identity y = x")
    ax.set(xlim=(lo-pad, hi+pad), ylim=(lo-pad, hi+pad),
           xlabel="Target SI (%)", ylabel="Predicted SI (%)", title=label)
    ax.set_aspect("equal", adjustable="box")
    ax.text(.04, .96, f"n={len(y)}\nMAE={metrics['mae']:.4f} SI pp\nRMSE={metrics['rmse']:.4f} SI pp\n"
            f"R²={metrics['r2']:.4f}\nMAPE={metrics['mape']:.2f}%", transform=ax.transAxes,
            va="top", fontsize=9, bbox={"facecolor": "white", "alpha": .9, "edgecolor": ".8"})
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=.2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    data = load_report(args.report_dir)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), layout="constrained")
    for ax, (key, label) in zip(axes, PROTOCOLS.items()):
        draw_scatter(ax, data.target_si.to_numpy(), data[key].to_numpy(), label, COLORS[key])
    fig.suptitle(f"Coronium V3.1 · Target versus prediction\n{SCOPE}")
    save_figure(fig, args.output_dir / "scatter")


if __name__ == "__main__":
    main()
