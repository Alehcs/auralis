"""Grad-CAM figure with the heatmap overlaid on the magnetogram.

Produces a two-panel figure:
    1. Raw signed magnetogram (B+ − B−), HMI-style grayscale.
    2. Same magnetogram with the Grad-CAM heatmap overlaid (alpha blend).

This single-overlay layout is an alternative to the three-panel
(B+ | B- | heatmap) decomposition; it shows the model's spatial attention
directly on the solar disk in one view.

Run from auralis-back/ (defaults to the high-activity hold-out sample
2024-08-12, SI≈2.90). Override with the GRADCAM_SAMPLE environment variable.

    python scripts/plot_gradcam_overlay.py
    GRADCAM_SAMPLE="2025.01.20" python scripts/plot_gradcam_overlay.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from scipy.ndimage import zoom

ROOT = Path(__file__).resolve().parent.parent  # auralis-back/
sys.path.insert(0, str(ROOT / "src"))
from models.train_model import CoroniumV3  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("auralis.gradcam_overlay")

WEIGHTS_PATH  = Path("models/best_coronium_v3_pro_augmented.pth")
DATA_DIR      = Path("data/processed")
OUTPUT_PATH   = Path("reports/figures/gradcam_overlay.png")
TARGET_LAYER  = "stage4"

# Default sample: highest-activity hold-out (2024-08-12, SI ≈ 2.90).
# Override with the GRADCAM_SAMPLE environment variable.
DEFAULT_SAMPLE = "2024.08.12"
TARGET_SAMPLE  = os.environ.get("GRADCAM_SAMPLE", DEFAULT_SAMPLE).strip() or DEFAULT_SAMPLE


# ---------------------------------------------------------------------------
# Grad-CAM hook plumbing
# ---------------------------------------------------------------------------
class GradCAMHook:
    """Captures activations and gradients on a target layer."""

    def __init__(self, model: nn.Module, layer_name: str) -> None:
        self.activations: torch.Tensor | None = None
        self.gradients:   torch.Tensor | None = None
        target = getattr(model, layer_name)
        self._handles = [
            target.register_forward_hook(self._fwd),
            target.register_full_backward_hook(self._bwd),
        ]

    def _fwd(self, module, inputs, output):
        self.activations = output.detach()

    def _bwd(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def remove(self) -> None:
        for h in self._handles:
            h.remove()


def compute_heatmap(model: nn.Module, x: torch.Tensor, hook: GradCAMHook,
                    target_size: Tuple[int, int]) -> Tuple[np.ndarray, float]:
    """Return (heatmap_normalized_to_[0,1], scalar_prediction)."""
    model.zero_grad(set_to_none=True)
    output = model(x)                            # shape (1, 1)
    scalar = output.squeeze()
    scalar.backward()

    grads = hook.gradients.mean(dim=(2, 3), keepdim=True)     # GAP gradients → (1, C, 1, 1)
    weighted = (grads * hook.activations).sum(dim=1).squeeze()  # → (H', W')
    cam = torch.relu(weighted).cpu().numpy()

    if cam.max() > 0:
        cam = cam / cam.max()

    z = target_size[0] / cam.shape[0]
    cam_full = zoom(cam, z, order=1)
    cam_full = np.clip(cam_full, 0.0, 1.0)
    return cam_full, float(scalar.detach().cpu().item())


# ---------------------------------------------------------------------------
# Sample loading
# ---------------------------------------------------------------------------
def load_sample(data_dir: Path, sample_token: str) -> Tuple[torch.Tensor, np.ndarray, str]:
    """Locate a magnetogram by substring, return (model_input, raw_2ch_array, filename)."""
    files = sorted(data_dir.glob("*_processed.npy"))
    if not files:
        raise FileNotFoundError(f"No *_processed.npy in {data_dir}")

    matches = [p for p in files if sample_token in p.name]
    if matches:
        path = matches[0]
        logger.info("Targeted sample: %s (token=%s)", path.name, sample_token)
    else:
        path = files[0]
        logger.warning("Token '%s' not found; falling back to %s", sample_token, path.name)

    arr = np.load(str(path)).astype(np.float32)

    # Legacy single-channel rescue: rebuild B+ / B- by ReLU split.
    if arr.ndim == 2:
        b_pos = np.maximum(0.0,  arr)
        b_neg = np.maximum(0.0, -arr)
        arr = np.stack([b_pos, b_neg], axis=0)

    tensor = torch.from_numpy(arr).unsqueeze(0).float()
    return tensor, arr, path.stem


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def plot_overlay(raw: np.ndarray, heatmap: np.ndarray,
                 prediction: float, sample_name: str,
                 output_path: Path) -> None:
    """Two-panel poster figure: raw magnetogram + Grad-CAM overlay."""
    # Reconstruct the signed magnetogram (B+ − B−).
    signed = raw[0] - raw[1]
    v = max(abs(signed.min()), abs(signed.max())) or 1.0
    vmin, vmax = -v, v

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor="white")

    # ── Panel 1: raw magnetogram (HMI grayscale, symmetric) ─────────────────
    ax1.imshow(signed, cmap="gray", origin="lower", vmin=vmin, vmax=vmax,
               interpolation="nearest")
    ax1.set_title("HMI Magnetogram (signed B = B⁺ − B⁻)",
                  fontsize=12, weight="bold")
    ax1.set_xticks([]); ax1.set_yticks([])
    for spine in ax1.spines.values():
        spine.set_edgecolor("#333")

    # ── Panel 2: magnetogram + Grad-CAM overlay ──────────────────────────────
    ax2.imshow(signed, cmap="gray", origin="lower", vmin=vmin, vmax=vmax,
               interpolation="nearest")
    overlay = ax2.imshow(heatmap, cmap="jet", origin="lower", alpha=0.55,
                        vmin=0.0, vmax=1.0)
    ax2.set_title(
        f"Grad-CAM attention (stage4) · ŷ = {prediction:+.3f}  (log-SI)",
        fontsize=12, weight="bold",
    )
    ax2.set_xticks([]); ax2.set_yticks([])
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333")

    # Colorbar for the heatmap.
    cbar = fig.colorbar(overlay, ax=ax2, fraction=0.046, pad=0.02)
    cbar.set_label("Grad-CAM activation", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle(
        f"Coronium V3 PRO · Where does the model look?\nSample: {sample_name}",
        fontsize=13, weight="bold", y=0.99,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Saved overlay figure → %s", output_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(f"Checkpoint missing: {WEIGHTS_PATH}")
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory missing: {DATA_DIR}")

    device = (
        torch.device("mps") if torch.backends.mps.is_available()
        else torch.device("cuda") if torch.cuda.is_available()
        else torch.device("cpu")
    )
    logger.info("Backend: %s", device)

    model = CoroniumV3(in_channels=2, dropout_rate=0.2)
    model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device,
                                     weights_only=True))
    model.to(device).eval()
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("Model loaded: %d parameters", n_params)

    x, raw, name = load_sample(DATA_DIR, TARGET_SAMPLE)
    x = x.to(device)

    hook = GradCAMHook(model, TARGET_LAYER)
    try:
        heatmap, prediction = compute_heatmap(model, x, hook, target_size=(512, 512))
    finally:
        hook.remove()

    logger.info("Prediction (log-SI proxy): %.4f", prediction)
    plot_overlay(raw, heatmap, prediction, name, OUTPUT_PATH)


if __name__ == "__main__":
    main()
