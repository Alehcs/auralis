"""Generate a poster-ready architecture diagram for Coronium V3 PRO.

Produces a block diagram showing the data flow:
    Input (2, 512, 512) dual-channel B+/B-
    → stage1 (32ch, 256x256) + ECA + Skip
    → stage2 (64ch, 128x128) + ECA + Skip
    → stage3 (96ch, 64x64)   + ECA + Skip
    → stage4 (128ch, 64x64)  + ECA + Skip  ← Grad-CAM hook
    → MaxPool stage4 → 32x32
    → Global Average Pooling → (128,)
    → Dropout(0.3) → Linear(128, 1)
    → log(SI) regression output

Run from auralis-back/:
    python scripts/plot_architecture_diagram.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT_PATH = Path("reports/figures/architecture_diagram.png")


# ---------------------------------------------------------------------------
# Palette — print-friendly, distinguishable in grayscale.
# ---------------------------------------------------------------------------
COLOR_INPUT      = "#FEE2B3"   # warm sand
COLOR_STAGE      = "#A7C7E7"   # light blue
COLOR_HOOK       = "#E5A6A6"   # rose (Grad-CAM hook)
COLOR_POOL       = "#C7BBE7"   # lavender
COLOR_HEAD       = "#A7E7C2"   # mint
COLOR_OUTPUT     = "#FFD6A5"   # soft peach
COLOR_ARROW      = "#374151"
COLOR_BORDER     = "#1F2937"
COLOR_BG_LABEL   = "#FAF8F4"

PARAMS = {
    "stage1": "32 ch · 4.4K",
    "stage2": "64 ch · 18K",
    "stage3": "96 ch · 60K",
    "stage4": "128 ch · 122K",
    "head":   "Linear(128→1)",
}


def add_block(ax, x, y, w, h, label, sub=None, color=COLOR_STAGE, border=None):
    """Draw a rounded rectangle with optional sub-label."""
    border = border or COLOR_BORDER
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.15",
        linewidth=1.4, edgecolor=border, facecolor=color, zorder=2,
    )
    ax.add_patch(box)
    if sub:
        ax.text(x + w/2, y + h*0.62, label, ha="center", va="center",
                fontsize=10, weight="bold", zorder=3)
        ax.text(x + w/2, y + h*0.28, sub, ha="center", va="center",
                fontsize=8.5, family="monospace", color="#1F2937", zorder=3)
    else:
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                fontsize=10, weight="bold", zorder=3)


def add_arrow(ax, x1, y1, x2, y2, label=None, label_offset=0.0):
    """Draw an arrow with optional label."""
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=1.4, color=COLOR_ARROW, zorder=1,
    )
    ax.add_patch(arr)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + label_offset
        ax.text(mx, my, label, ha="center", va="center", fontsize=7.5,
                color="#374151", style="italic",
                bbox=dict(boxstyle="round,pad=0.18",
                          facecolor=COLOR_BG_LABEL, edgecolor="none", alpha=0.95),
                zorder=4)


def main() -> None:
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Title ────────────────────────────────────────────────────────────────
    ax.text(8, 6.55, "Coronium V3 PRO — Architecture", ha="center", va="center",
            fontsize=16, weight="bold")
    ax.text(8, 6.15,
            "Lightweight residual CNN · 206,875 params · ONNX 86.6 KB · 25.11 ms CPU",
            ha="center", va="center", fontsize=10, color="#4B5563", style="italic")

    # ── Input block ──────────────────────────────────────────────────────────
    add_block(ax, 0.2, 2.9, 1.7, 1.4, "Input", "(2, 512, 512)",
              color=COLOR_INPUT)
    ax.text(1.05, 2.4, "B⁺ · B⁻\nsign(x)·log1p(|x|)",
            ha="center", va="top", fontsize=7.5, style="italic", color="#374151")

    # ── 4 Residual stages ────────────────────────────────────────────────────
    stage_x  = [2.7, 5.4, 8.1, 10.8]
    stage_h_dims = ["256²", "128²", "64²", "64²"]   # spatial after maxpool of each stage
    stage_filters = [32, 64, 96, 128]
    stage_params  = ["4.4K", "18K", "60K", "122K"]

    for i, (x, h_dim, f, p) in enumerate(
        zip(stage_x, stage_h_dims, stage_filters, stage_params)
    ):
        is_last = (i == 3)
        color = COLOR_HOOK if is_last else COLOR_STAGE
        add_block(ax, x, 2.7, 2.0, 1.8,
                  f"stage{i+1}",
                  f"{f} ch · {h_dim}\n{p} params",
                  color=color)
        # Sub-annotation: ECA + Skip
        ax.text(x + 1.0, 2.45, "ECA + Skip + Dropout2d",
                ha="center", va="top", fontsize=7, style="italic", color="#374151")

        # arrow into the block
        if i == 0:
            add_arrow(ax, 1.95, 3.6, x - 0.05, 3.6,
                      label="Conv 3×3\nResidual", label_offset=0.55)
        else:
            add_arrow(ax, stage_x[i-1] + 2.05, 3.6, x - 0.05, 3.6,
                      label="MaxPool 2×2", label_offset=0.45)

    # ── Grad-CAM hook annotation on stage4 ──────────────────────────────────
    ax.annotate(
        "Grad-CAM\nhook",
        xy=(11.8, 4.5), xytext=(11.8, 5.55),
        ha="center", fontsize=8.5, weight="bold", color="#9B1C1C",
        arrowprops=dict(arrowstyle="-|>", color="#9B1C1C", lw=1.3),
    )

    # ── GAP + Head ───────────────────────────────────────────────────────────
    add_arrow(ax, 12.85, 3.6, 13.4, 3.6, label="MaxPool", label_offset=0.45)
    add_block(ax, 13.4, 2.9, 1.0, 1.4, "GAP", "(128,)",
              color=COLOR_POOL)

    add_arrow(ax, 14.4, 3.6, 14.85, 3.6)
    add_block(ax, 14.85, 2.9, 1.05, 1.4, "Head", "Drop(0.3)\nLin(128,1)",
              color=COLOR_HEAD)

    # ── Output ───────────────────────────────────────────────────────────────
    add_arrow(ax, 8, 2.5, 8, 1.65, label="", label_offset=0.0)
    add_block(ax, 6.3, 0.6, 3.4, 1.0,
              "Predicted activity index   ŷ ∈ log-SI ≈ [1.22, 2.98]",
              color=COLOR_OUTPUT)

    # Move output arrow to come from head
    # (re-draw to ensure correct origin from Head block bottom)
    ax.patches[-2].remove()  # remove placeholder arrow
    add_arrow(ax, 15.37, 2.85, 15.37, 1.3)
    add_arrow(ax, 15.30, 1.10, 9.75, 1.10, label="ŷ (log-SI)", label_offset=0.20)

    # ── Loss / training annotation (bottom-left footer) ─────────────────────
    ax.text(0.2, 0.55,
            "Loss:  WeightedHuberLoss (δ=1.0, α=2.0) + L1 in log-SI space\n"
            "Train: AdamW, lr=1e-3 → ReduceLROnPlateau · MC Dropout T=20 at eval",
            ha="left", va="top", fontsize=8, color="#4B5563", family="monospace")

    # ── Save ─────────────────────────────────────────────────────────────────
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Architecture diagram saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
