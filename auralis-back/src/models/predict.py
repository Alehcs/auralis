"""Inference engine for Coronium V2 PRO.

Provides a standalone CLI and importable functions for end-to-end prediction
on raw HMI FITS files: load → preprocess → infer → visualise.

The preprocessing chain must mirror the training pipeline in
``prepare_dataset`` exactly — NaN fill → bilinear resample → ±400 G clip →
[-1, 1] normalisation. Any deviation introduces distribution shift between
training and inference inputs that cannot be detected at runtime.
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import torch
import sunpy.map
from skimage.transform import resize

from train_model import Coronium, get_device


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


def preprocess_fits_image(
    fits_path: Path,
    target_size: int = 512,
    clip_value: float = 400.0,
) -> Tuple[torch.Tensor, "sunpy.map.Map"]:
    """Load and normalise a raw HMI FITS file for model inference.

    The normalisation chain must be identical to the one applied in
    ``prepare_dataset.load_and_process_magnetogram`` to avoid distribution
    shift between training data and inference inputs:

    - NaN fill: off-disk pixels carry NaN in HMI Level-1.5 data because the
      solar limb mask is applied upstream by JSOC. Replacing with 0 is correct
      because 0 G is the quiet-Sun background field.
    - Clip at ±400 G: covers the functional range of plage and network fields
      while saturating umbral core pixels that represent < 0.1% of the disk
      area and would otherwise compress the dynamic range of the normalised
      array. This threshold follows Bobra & Couvidat (2015).
    - Scale by 1 / clip_value: maps the clipped range linearly to [-1, 1],
      matching the float32 tensors written by the batch preprocessing pipeline.

    Args:
        fits_path: Absolute path to an HMI Level-1.5 FITS file.
        target_size: Square output resolution in pixels. Must match the
            resolution used during training (default 512).
        clip_value: Symmetric saturation bound in Gauss (default 400.0).

    Returns:
        Tuple of:
            - Tensor of shape (1, 1, H, W), dtype float32, ready for a
              model forward pass.
            - ``sunpy.map.Map`` object retaining the original FITS header for
              downstream visualisation with a heliographic coordinate grid.
    """
    logger.info("Preprocessing: %s", fits_path.name)

    solar_map = sunpy.map.Map(str(fits_path))
    data = solar_map.data

    data = np.nan_to_num(data, nan=0.0)
    logger.info(
        "  Original shape: %s  |  range: [%.2f, %.2f] G",
        data.shape, np.min(data), np.max(data),
    )

    data_resampled = resize(
        data,
        (target_size, target_size),
        mode="reflect",
        anti_aliasing=True,
        preserve_range=True,
    )
    data_resampled = np.nan_to_num(data_resampled, nan=0.0)

    data_normalized = np.clip(data_resampled, -clip_value, clip_value) / clip_value

    tensor = torch.from_numpy(data_normalized).float().unsqueeze(0).unsqueeze(0)
    logger.info("  Output tensor shape: %s", tuple(tensor.shape))

    return tensor, solar_map


def load_model(
    model_path: str = "models/coronium_best.pth",
    device: Optional[torch.device] = None,
) -> Tuple[Coronium, torch.device]:
    """Instantiate Coronium and load a saved state dictionary.

    ``model.eval()`` switches BatchNorm layers to use running statistics
    accumulated during training and disables Dropout2d, giving deterministic
    output for a fixed input. Monte Carlo Dropout uncertainty estimation
    requires re-enabling training mode in the calling code before iterating
    over stochastic forward passes.

    Args:
        model_path: Path to a ``.pth`` checkpoint written by ``train_model``.
        device: Target device. Detected automatically if ``None``.

    Returns:
        Tuple of (loaded Coronium in eval mode, resolved torch.device).

    Raises:
        FileNotFoundError: If ``model_path`` does not exist on disk.
    """
    if device is None:
        device = get_device()

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Checkpoint not found: {model_path}")

    logger.info("Loading checkpoint: %s", model_path)

    model = Coronium(dropout_rate=0.3)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    logger.info("Model loaded: %d parameters  |  device: %s", total_params, device)

    return model, device


def predict_sunspot_index(
    model: Coronium,
    image_tensor: torch.Tensor,
    device: torch.device,
) -> float:
    """Run a single deterministic forward pass and return the scalar prediction.

    ``torch.no_grad()`` disables autograd during inference to reduce memory
    consumption. For Monte Carlo Dropout uncertainty estimation, call this
    function with ``model.train()`` active and aggregate outputs over N draws
    to obtain a predictive mean and variance.

    Args:
        model: Coronium instance in eval mode (or train mode for MC Dropout).
        image_tensor: Preprocessed tensor of shape (1, 1, H, W).
        device: Device on which both model and tensor are resident.

    Returns:
        Predicted sunspot index as a Python float.
    """
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        prediction = model(image_tensor)

    predicted_index: float = prediction.item()
    logger.info("Prediction: %.4f", predicted_index)

    return predicted_index


def get_real_sunspot_index(
    filename: str,
    metadata_csv: str = "data/processed/metadata_processed.csv",
) -> Optional[float]:
    """Retrieve the ground-truth sunspot index for a given filename.

    The CSV produced by ``prepare_dataset`` contains one row per processed
    magnetogram with the sunspot index computed on the raw (pre-normalised)
    pixel array, so values are in percentage units consistent with the model
    output scale.

    Args:
        filename: Stem of the FITS file (without extension), used as the
            lookup key against the ``filename`` column of the metadata CSV.
        metadata_csv: Path to the metadata CSV.

    Returns:
        Ground-truth sunspot index as a float, or ``None`` if the file is
        absent from the metadata table.
    """
    if not Path(metadata_csv).exists():
        logger.warning("Metadata CSV not found: %s", metadata_csv)
        return None

    metadata = pd.read_csv(metadata_csv)
    match = metadata[metadata["filename"] == filename]

    if match.empty:
        logger.warning("'%s' not found in metadata.", filename)
        return None

    real_index: float = match.iloc[0]["sunspot_index"]
    logger.info("Ground truth: %.4f", real_index)

    return real_index


def visualize_prediction(
    solar_map: "sunpy.map.Map",
    predicted_index: float,
    real_index: Optional[float] = None,
    output_path: str = "reports/figures/prediction_result.png",
) -> None:
    """Render the magnetogram with prediction annotations and save to disk.

    The HMI colormap ('hmimag') uses a diverging red-blue palette centred at
    0 G, following the SDO/HMI team convention for LOS magnetograms. The
    display range is clamped to ±200 G to reveal quiet-Sun network structure;
    this does not affect the model input, which was clipped at ±400 G.

    Args:
        solar_map: ``sunpy.map.Map`` instance from the original FITS file,
            used to draw the heliographic coordinate grid.
        predicted_index: Model output as a Python float.
        real_index: Ground-truth value for residual annotation; omitted if
            ``None``.
        output_path: Filesystem path for the saved PNG (parent created if
            absent).
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection=solar_map)

    norm = Normalize(vmin=-200, vmax=200)
    solar_map.plot(axes=ax, cmap="hmimag", norm=norm)
    solar_map.draw_grid(axes=ax, color="white", alpha=0.4, linewidth=0.5)

    obs_time = solar_map.date.strftime("%Y-%m-%d %H:%M:%S")
    if real_index is not None:
        error = abs(predicted_index - real_index)
        error_pct = (error / real_index) * 100 if real_index > 0 else 0.0
        title = (
            f"SDO/HMI LOS Magnetogram — {obs_time} UTC\n"
            f"Ground truth: {real_index:.4f}  |  Predicted: {predicted_index:.4f}  "
            f"|  |Error|: {error:.4f} ({error_pct:.2f}%)"
        )
    else:
        title = (
            f"SDO/HMI LOS Magnetogram — {obs_time} UTC\n"
            f"Predicted sunspot index: {predicted_index:.4f}"
        )

    ax.set_title(title, fontsize=11)

    cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.046, pad=0.08)
    cbar.set_label("LOS Magnetic Field (Gauss)", rotation=270, labelpad=25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info("Visualisation saved: %s", output_path)
    plt.close()


def main() -> None:
    """CLI entry point for single-image inference."""
    parser = argparse.ArgumentParser(
        description="Coronium V2 PRO — sunspot index inference on HMI FITS files"
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Path to an HMI FITS file. Defaults to the first file in data/raw/.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/coronium_best.pth",
        help="Path to a trained checkpoint (default: models/coronium_best.pth).",
    )
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Auralis — Coronium Inference")
    logger.info("=" * 70)

    if args.image:
        image_path = Path(args.image)
    else:
        raw_files = sorted(Path("data/raw").glob("*.fits"))
        if not raw_files:
            logger.error("No FITS files found in data/raw/")
            return
        image_path = raw_files[0]
        logger.info("Defaulting to: %s", image_path.name)

    if not image_path.exists():
        logger.error("File not found: %s", image_path)
        return

    model, device = load_model(args.model)
    image_tensor, solar_map = preprocess_fits_image(image_path)
    predicted_index = predict_sunspot_index(model, image_tensor, device)
    real_index = get_real_sunspot_index(image_path.stem)
    visualize_prediction(solar_map, predicted_index, real_index)

    logger.info("=" * 70)
    logger.info("Results  |  File: %s", image_path.name)
    logger.info("Predicted sunspot index: %.4f", predicted_index)

    if real_index is not None:
        error = abs(predicted_index - real_index)
        error_pct = (error / real_index) * 100 if real_index > 0 else 0.0
        logger.info("Ground truth:           %.4f", real_index)
        logger.info("Absolute error:         %.4f", error)
        logger.info("Relative error:         %.2f%%", error_pct)

    logger.info("=" * 70)
    logger.info("Inference complete.")


if __name__ == "__main__":
    main()
