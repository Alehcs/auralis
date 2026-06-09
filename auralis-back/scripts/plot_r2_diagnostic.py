"""Generate the R² diagnostic figure for Coronium V3 PRO.

Two-panel layout:
    1. Predicted vs. real with the identity line and 1-σ residual band.
    2. Residual distribution (predicted − real) with mean / std annotations.

Inputs : reports/results_comparison.csv  (produced by scripts/evaluate_final.py)
Outputs: reports/r2_diagnostic.png

Run from auralis-back/:
    python scripts/plot_r2_diagnostic.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CSV_PATH    = Path("reports/results_comparison.csv")
OUTPUT_PATH = Path("reports/r2_diagnostic.png")


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Predictions CSV not found at {CSV_PATH}. "
            "Run scripts/evaluate_final.py first."
        )

    df = pd.read_csv(CSV_PATH)
    y_real = df["Real_SSN"].to_numpy()
    y_pred = df["Predicted_SSN"].to_numpy()
    residuals = y_pred - y_real

    # Metrics in log-SI space (same as the master eval).
    mae  = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_real - y_real.mean()) ** 2))
    r2     = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # ── Panel 1: Predicted vs Real ───────────────────────────────────────────
    lo = float(min(y_real.min(), y_pred.min())) - 0.1
    hi = float(max(y_real.max(), y_pred.max())) + 0.1

    ax1.scatter(y_real, y_pred, s=18, alpha=0.55, color="#1f77b4",
                edgecolor="white", linewidth=0.3)
    ax1.plot([lo, hi], [lo, hi], "k--", linewidth=1.0,
             label="Identidad y = x")

    # 1-σ residual band around the identity line.
    sigma = float(np.std(residuals))
    ax1.fill_between([lo, hi], [lo - sigma, hi - sigma], [lo + sigma, hi + sigma],
                     color="grey", alpha=0.12, label=f"Banda ±σ ({sigma:.3f})")

    ax1.set_xlabel("Real SSN (log-SI)", fontsize=11)
    ax1.set_ylabel("Predicted SSN (log-SI)", fontsize=11)
    ax1.set_title(f"Predicted vs. Real  ·  R² = {r2:.4f}", fontsize=12, weight="bold")
    ax1.set_xlim(lo, hi)
    ax1.set_ylim(lo, hi)
    ax1.set_aspect("equal", adjustable="box")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left", fontsize=9, frameon=True)

    # Metric annotation box.
    txt = f"MAE  = {mae:.4f}\nRMSE = {rmse:.4f}\nR²   = {r2:.4f}\nN    = {len(df)}"
    ax1.text(0.97, 0.05, txt, transform=ax1.transAxes, ha="right", va="bottom",
             family="monospace", fontsize=9,
             bbox=dict(boxstyle="round,pad=0.4",
                       facecolor="white", edgecolor="grey", alpha=0.9))

    # ── Panel 2: Residual distribution ───────────────────────────────────────
    ax2.hist(residuals, bins=30, color="#ff7f0e", edgecolor="white", alpha=0.85)
    ax2.axvline(0.0, color="black", linestyle="-", linewidth=1.0, label="Sin sesgo")
    ax2.axvline(float(residuals.mean()), color="red", linestyle="--", linewidth=1.2,
                label=f"Media residuos = {residuals.mean():+.4f}")

    ax2.set_xlabel("Residuo  (Predicted − Real)  [log-SI]", fontsize=11)
    ax2.set_ylabel("Frecuencia", fontsize=11)
    ax2.set_title("Distribución de residuos", fontsize=12, weight="bold")
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.legend(loc="upper right", fontsize=9, frameon=True)

    fig.suptitle("Coronium V3 PRO · Diagnóstico de regresión sobre 353 muestras hold-out",
                 fontsize=13, weight="bold")
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"R² diagnostic saved to: {OUTPUT_PATH}")
    print(f"  MAE={mae:.4f}  RMSE={rmse:.4f}  R2={r2:.4f}  N={len(df)}")


if __name__ == "__main__":
    main()
