"""Autopsia visual: genera evidencia del Mode Collapse en SolarNetV3 PRO.

Lee reports/results_comparison.csv y produce un scatter plot que muestra
cómo la predicción colapsa en el promedio (~1.51) mientras los valores
reales de sunspot_index varían dinámicamente a lo largo de la muestra.

Salida: reports/figures/mode_collapse_evidence.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd


CSV_PATH = Path("HeliosPipeline/reports/results_comparison.csv")
OUT_PATH = Path("HeliosPipeline/reports/figures/mode_collapse_evidence.png")


def main() -> None:
    # ── 1. Cargar datos ──────────────────────────────────────────────────────
    df = pd.read_csv(CSV_PATH)
    n = len(df)
    idx = np.arange(n)

    real = df["Real_SSN"].values
    pred = df["Predicted_SSN"].values
    pred_mean = pred.mean()

    # ── 2. Figura ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")

    # Valores reales — scatter con transparencia para mostrar densidad
    ax.scatter(
        idx, real,
        color="#58a6ff", alpha=0.55, s=12,
        label=f"Real SSN  (σ={real.std():.3f})",
        zorder=3,
    )

    # Predicción colapsada — línea roja plana
    ax.scatter(
        idx, pred,
        color="#ff7b72", alpha=0.35, s=8,
        label=f"Predicted SSN  (σ={pred.std():.4f})",
        zorder=2,
    )
    ax.axhline(
        pred_mean,
        color="#ff7b72", linewidth=2.0, linestyle="--", alpha=0.9,
        label=f"Predicted mean ≈ {pred_mean:.4f}",
        zorder=4,
    )

    # Anotación explicativa
    ax.annotate(
        f"Mode Collapse\nμ_pred ≈ {pred_mean:.4f}",
        xy=(n * 0.5, pred_mean),
        xytext=(n * 0.5, pred_mean + (real.max() - pred_mean) * 0.35),
        fontsize=10, color="#ff7b72",
        arrowprops=dict(arrowstyle="->", color="#ff7b72", lw=1.5),
        ha="center",
        bbox=dict(boxstyle="round,pad=0.3", fc="#21262d", ec="#ff7b72", alpha=0.85),
    )

    # Métricas en el corner
    r2 = 1 - np.sum((real - pred) ** 2) / np.sum((real - real.mean()) ** 2)
    mae = np.abs(real - pred).mean()
    stats_text = f"R²  = {r2:.3f}\nMAE = {mae:.4f}"
    ax.text(
        0.98, 0.97, stats_text,
        transform=ax.transAxes,
        fontsize=10, color="#e6edf3",
        va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.4", fc="#21262d", ec="#30363d", alpha=0.9),
    )

    # ── 3. Estética ──────────────────────────────────────────────────────────
    ax.set_title(
        "Evidencia de Mode Collapse: Predicción estancada en el promedio",
        fontsize=15, fontweight="bold", color="#e6edf3", pad=14,
    )
    ax.set_xlabel("Índice de muestra", fontsize=12, color="#8b949e")
    ax.set_ylabel("Sunspot Index (SSN)", fontsize=12, color="#8b949e")

    ax.tick_params(colors="#8b949e")
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    ax.legend(
        fontsize=10, framealpha=0.85,
        facecolor="#21262d", edgecolor="#30363d", labelcolor="#e6edf3",
    )
    ax.grid(axis="y", color="#30363d", linewidth=0.6, linestyle=":")

    plt.tight_layout()

    # ── 4. Guardar ───────────────────────────────────────────────────────────
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Figura guardada en: {OUT_PATH}")


if __name__ == "__main__":
    main()
