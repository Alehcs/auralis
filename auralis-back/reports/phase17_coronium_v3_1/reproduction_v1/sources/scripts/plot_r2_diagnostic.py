"""Residual diagnostics in SI percentage points, reused by run_phase17.py.

python scripts/plot_r2_diagnostic.py --report-dir <phase17-run> --output-dir <fresh-dir>
No residual standard deviation band is presented as predictive uncertainty.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_final_scatter import PROTOCOLS, COLORS, SCOPE, load_report, save_figure


def draw_residual_histogram(ax, residual, bins, label, color):
    ax.hist(residual, bins=bins, color=color, alpha=.8, edgecolor="white")
    ax.axvline(0, color="black", lw=1)
    ax.axvline(residual.mean(), color="black", ls="--", label=f"Bias {residual.mean():+.4f} SI pp")
    ax.set(xlabel="Residual = prediction − target (SI pp)", ylabel="Observations", title=label)
    ax.legend(fontsize=9)
    ax.grid(alpha=.2, axis="y")


def draw_residual_scatter(ax, x, residual, xlabel, label, color):
    ax.scatter(x, residual, s=17, alpha=.65, color=color, edgecolors="none")
    ax.axhline(0, color="black", ls="--", lw=1)
    ax.set(xlabel=xlabel, ylabel="Residual = prediction − target (SI pp)", title=label)
    ax.grid(alpha=.2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    data = load_report(args.report_dir)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    residuals = {key: (data[key] - data.target_si).to_numpy() for key in PROTOCOLS}
    bins = np.histogram_bin_edges(np.concatenate(list(residuals.values())), bins="fd")
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    for (key, label), row in zip(PROTOCOLS.items(), axes):
        draw_residual_scatter(row[0], data[key], residuals[key], "Predicted SI (%)", label, COLORS[key])
        draw_residual_histogram(row[1], residuals[key], bins, label, COLORS[key])
    fig.suptitle(f"Coronium V3.1 · Regression diagnostics\n{SCOPE}")
    save_figure(fig, args.output_dir / "residual_diagnostics")


if __name__ == "__main__":
    main()
