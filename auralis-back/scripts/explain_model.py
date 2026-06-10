"""Generate a Grad-CAM explanation figure for Coronium V3 PRO.

The model is a scalar regressor, so the backward target is the predicted index
itself. Hooks target ``stage4``, the last spatial block before global pooling.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from models.train_model import CoroniumV3  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("auralis.gradcam")


WEIGHTS_PATH = Path("models/best_coronium_v3_pro_augmented.pth")
DATA_DIR = Path("data/processed")
OUTPUT_FIGURE = Path("reports/figures/gradcam_sample.png")

# Optional: target a specific sample for the Grad-CAM. Override via env var
# GRADCAM_SAMPLE (e.g. "hmi.m_45s.2024.08.12_00_01_30_TAI"). If unset or no
# match, falls back to the first .npy in DATA_DIR (legacy behaviour).
import os
TARGET_SAMPLE = os.environ.get("GRADCAM_SAMPLE", "").strip() or None

# Last convolutional stage before global average pooling. Earlier layers keep
# more spatial detail, but stage4 carries the semantic signal the regressor
# actually uses for the final index.
TARGET_LAYER_NAME = "stage4"
DROPOUT_RATE = 0.2


class GradCAMHookManager:
    """Owns Grad-CAM hooks and removes them after use.

    Leaving hooks attached across repeated calls can duplicate captures, which
    is especially confusing when this script is imported from a notebook.
    """

    def __init__(self, model: nn.Module, layer_name: str) -> None:
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._handles: list = []

        if not hasattr(model, layer_name):
            children = [name for name, _ in model.named_children()]
            raise AttributeError(
                f"Model has no layer named '{layer_name}'. Available top-level "
                f"modules: {children}"
            )

        target_layer: nn.Module = getattr(model, layer_name)

        def save_activations(
            module: nn.Module,
            inputs: Tuple[torch.Tensor, ...],
            output: torch.Tensor,
        ) -> None:
            self.activations = output.detach().cpu()

        def save_gradients(
            module: nn.Module,
            grad_input: Tuple[Optional[torch.Tensor], ...],
            grad_output: Tuple[torch.Tensor, ...],
        ) -> None:
            self.gradients = grad_output[0].detach().cpu()

        self._handles.append(target_layer.register_forward_hook(save_activations))
        self._handles.append(target_layer.register_full_backward_hook(save_gradients))
        logger.info(
            "Registered Grad-CAM hooks on model.%s (%s)",
            layer_name,
            type(target_layer).__name__,
        )

    def remove(self) -> None:
        """Detach hooks so later model calls are not affected by this script."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()


def compute_gradcam(
    model: nn.Module,
    input_tensor: torch.Tensor,
    hook_manager: GradCAMHookManager,
    target_size: Tuple[int, int] = (512, 512),
) -> Tuple[np.ndarray, float]:
    """Compute a normalized Grad-CAM heatmap for one processed magnetogram.

    Because the model is a scalar regressor, the backward target is the
    prediction itself, not a class score.
    """
    model.eval()

    output = model(input_tensor)
    prediction = float(output.item())
    logger.info("Model prediction: %.6f (normalized proxy index)", prediction)

    model.zero_grad()
    output.squeeze().backward()

    activations = hook_manager.activations
    gradients = hook_manager.gradients
    if activations is None or gradients is None:
        raise RuntimeError(
            "Grad-CAM hooks did not capture activations and gradients. "
            f"Check TARGET_LAYER_NAME='{TARGET_LAYER_NAME}'."
        )

    channel_weights = gradients.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((channel_weights * activations).sum(dim=1, keepdim=True))
    cam = F.interpolate(
        cam,
        size=target_size,
        mode="bilinear",
        align_corners=False,
    )

    heatmap = cam.squeeze().numpy()
    heat_min = float(heatmap.min())
    heat_max = float(heatmap.max())
    if heat_max - heat_min > 1e-8:
        heatmap = (heatmap - heat_min) / (heat_max - heat_min)
    else:
        # Quiet-Sun examples can produce a nearly flat attribution map. Returning
        # zeros is clearer than amplifying numerical noise into a false hot spot.
        heatmap = np.zeros_like(heatmap)
        logger.warning("Grad-CAM heatmap is nearly constant; returning zeros.")

    logger.info(
        "Computed Grad-CAM heatmap: %s -> %s",
        tuple(activations.shape[2:]),
        target_size,
    )
    return heatmap.astype(np.float32), prediction


def load_sample(data_dir: Path) -> Tuple[torch.Tensor, np.ndarray, str]:
    """Load the first processed tensor and adapt legacy single-channel data."""

    npy_files = sorted(data_dir.glob("*_processed.npy"))
    if not npy_files:
        raise FileNotFoundError(
            f"No *_processed.npy files found in {data_dir}. "
            "Run src/processing/prepare_dataset.py first."
        )

    # Targeted selection takes precedence over the legacy first-file behaviour.
    sample_path = npy_files[0]
    if TARGET_SAMPLE:
        matches = [p for p in npy_files if TARGET_SAMPLE in p.name]
        if matches:
            sample_path = matches[0]
            logger.info("Targeted sample matched: %s", sample_path.name)
        else:
            logger.warning(
                "TARGET_SAMPLE='%s' did not match any file in %s; "
                "falling back to first file.",
                TARGET_SAMPLE, data_dir,
            )
    image = np.load(str(sample_path)).astype(np.float32)
    logger.info(
        "Selected sample: %s | shape=%s | dtype=%s",
        sample_path.name,
        image.shape,
        image.dtype,
    )

    if image.ndim == 2:
        b_pos = np.maximum(0.0, image)
        b_neg = np.maximum(0.0, -image)
        image = np.stack([b_pos, b_neg], axis=0).astype(np.float32)
        logger.info("Converted legacy single-channel tensor to B+/B- format.")

    if image.ndim != 3 or image.shape[0] != 2:
        raise ValueError(
            f"Expected a processed tensor with shape (2, H, W); got {image.shape}."
        )

    input_tensor = torch.from_numpy(image).float().unsqueeze(0)
    return input_tensor, image, sample_path.stem


def plot_gradcam(
    raw_channels: np.ndarray,
    heatmap: np.ndarray,
    prediction: float,
    sample_name: str,
    output_path: Path,
) -> None:
    """Render B+, B-, and Grad-CAM over magnetic magnitude into one figure."""
    b_pos = raw_channels[0]
    b_neg = raw_channels[1]
    b_mag = b_pos + b_neg
    b_mag_norm = b_mag / (float(b_mag.max()) + 1e-8)

    dark_bg = "#0d0d0d"
    fig = plt.figure(figsize=(19, 6.5), facecolor=dark_bg)
    fig.suptitle(
        f"Grad-CAM - Coronium V3 PRO\n"
        f"Sample: {sample_name}     "
        f"Prediction (normalized proxy index): {prediction:+.5f}",
        fontsize=12,
        color="white",
        fontweight="bold",
        y=1.03,
    )

    grid = gridspec.GridSpec(
        1,
        3,
        figure=fig,
        wspace=0.10,
        left=0.04,
        right=0.97,
    )

    ax1 = fig.add_subplot(grid[0])
    im1 = ax1.imshow(
        b_pos,
        cmap="hot",
        origin="lower",
        aspect="equal",
        interpolation="nearest",
    )
    ax1.set_title("Magnetogram B+\n(positive polarity lobe)", color="white", fontsize=10)
    ax1.set_xlabel("Pixel X [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax1.set_ylabel("Pixel Y [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax1.tick_params(colors="#aaaaaa", labelsize=7)
    ax1.set_facecolor(dark_bg)
    for spine in ax1.spines.values():
        spine.set_edgecolor("#444444")
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("B+ flux [a.u., log-normalized]", color="#aaaaaa", fontsize=7)
    cbar1.ax.yaxis.set_tick_params(color="#aaaaaa", labelsize=7)
    plt.setp(cbar1.ax.yaxis.get_ticklabels(), color="#aaaaaa")

    ax2 = fig.add_subplot(grid[1])
    im2 = ax2.imshow(
        b_neg,
        cmap="cool",
        origin="lower",
        aspect="equal",
        interpolation="nearest",
    )
    ax2.set_title("Magnetogram B-\n(negative polarity lobe)", color="white", fontsize=10)
    ax2.set_xlabel("Pixel X [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax2.tick_params(colors="#aaaaaa", labelsize=7)
    ax2.set_facecolor(dark_bg)
    for spine in ax2.spines.values():
        spine.set_edgecolor("#444444")
    cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("B- flux [a.u., log-normalized]", color="#aaaaaa", fontsize=7)
    cbar2.ax.yaxis.set_tick_params(color="#aaaaaa", labelsize=7)
    plt.setp(cbar2.ax.yaxis.get_ticklabels(), color="#aaaaaa")

    ax3 = fig.add_subplot(grid[2])
    ax3.imshow(
        b_mag_norm,
        cmap="gray",
        origin="lower",
        aspect="equal",
        interpolation="nearest",
        alpha=1.0,
    )
    im3 = ax3.imshow(
        heatmap,
        cmap="jet",
        origin="lower",
        aspect="equal",
        interpolation="bilinear",
        alpha=0.55,
        vmin=0.0,
        vmax=1.0,
    )
    ax3.set_title(
        "Grad-CAM over |B| = B+ + B-\n(regions increasing the model prediction)",
        color="white",
        fontsize=10,
    )
    ax3.set_xlabel("Pixel X [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax3.tick_params(colors="#aaaaaa", labelsize=7)
    ax3.set_facecolor(dark_bg)
    for spine in ax3.spines.values():
        spine.set_edgecolor("#444444")
    cbar3 = fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
    cbar3.set_label("Grad-CAM importance [0 low, 1 high]", color="#aaaaaa", fontsize=7)
    cbar3.ax.yaxis.set_tick_params(color="#aaaaaa", labelsize=7)
    plt.setp(cbar3.ax.yaxis.get_ticklabels(), color="#aaaaaa")

    ax3.text(
        0.01,
        0.01,
        "L_GC = ReLU(sum_k alpha_k * A_k) | alpha_k = GAP(dy/dA_k)",
        transform=ax3.transAxes,
        fontsize=6.5,
        color="#888888",
        verticalalignment="bottom",
        fontfamily="monospace",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        str(output_path),
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    logger.info("Saved Grad-CAM figure: %s", output_path)


def get_device() -> torch.device:
    """Select the best available backend for the backward pass."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Backend: CUDA - %s", torch.cuda.get_device_name(0))
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Backend: MPS (Apple Silicon)")
    else:
        device = torch.device("cpu")
        logger.info("Backend: CPU")
    return device


def main() -> None:
    """Run the complete Grad-CAM pipeline and write the figure artifact."""
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {WEIGHTS_PATH}. "
            "Run training or place the augmented checkpoint under models/."
        )
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Processed data directory not found: {DATA_DIR}. "
            "Run src/processing/prepare_dataset.py first."
        )

    device = get_device()
    model = CoroniumV3(in_channels=2, dropout_rate=DROPOUT_RATE)
    state_dict = torch.load(WEIGHTS_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    total_params = sum(param.numel() for param in model.parameters())
    logger.info(
        "Loaded CoroniumV3 PRO: %d parameters | eval mode | device=%s",
        total_params,
        device,
    )

    input_tensor, raw_channels, sample_name = load_sample(DATA_DIR)
    input_tensor = input_tensor.to(device)

    hook_manager = GradCAMHookManager(model, TARGET_LAYER_NAME)
    try:
        heatmap, prediction = compute_gradcam(
            model=model,
            input_tensor=input_tensor,
            hook_manager=hook_manager,
            target_size=(512, 512),
        )
    finally:
        hook_manager.remove()

    plot_gradcam(
        raw_channels=raw_channels,
        heatmap=heatmap,
        prediction=prediction,
        sample_name=sample_name,
        output_path=OUTPUT_FIGURE,
    )

    logger.info("=" * 62)
    logger.info("Grad-CAM pipeline completed.")
    logger.info("Target layer : model.%s (V3ResidualBlock 96 -> 128)", TARGET_LAYER_NAME)
    logger.info("CAM size     : (64, 64) -> (512, 512)")
    logger.info("Figure       : %s", OUTPUT_FIGURE)
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
