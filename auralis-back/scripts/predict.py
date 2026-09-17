"""FITS/NPY inference CLI for the selected verified clip400/SI release."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import torch


ROOT = Path(__file__).resolve().parent.parent  # auralis-back/
sys.path.insert(0, str(ROOT / "src"))
from models.train_model import CoroniumV3 as Coronium  # noqa: E402
from processing.model_input import normalize_field, prepare_model_input
from models import serving_selection as serving


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
    """Apply the same clip400/polarity transformation as evaluation and the API."""
    logger.info("Preprocessing: %s", fits_path.name)

    import sunpy.map
    solar_map = sunpy.map.Map(str(fits_path))
    data = solar_map.data

    data = np.nan_to_num(data, nan=0.0)
    logger.info(
        "  Original shape: %s  |  range: [%.2f, %.2f] G",
        data.shape, np.min(data), np.max(data),
    )

    if target_size != 512 or clip_value != 400.0:
        raise ValueError("Promoted checkpoint requires 512 px and clip_value=400 G")
    data_normalized = normalize_field(data, target_size, clip_value)
    tensor = torch.from_numpy(prepare_model_input(data_normalized))[None]
    logger.info("  Output tensor shape: %s", tuple(tensor.shape))

    return tensor, solar_map


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_model(
    model_path: Optional[str] = None,
    device: Optional[torch.device] = None,
) -> Tuple[Coronium, torch.device]:
    """Load the promoted Coronium checkpoint in deterministic eval mode."""
    serving.load_release()
    model_path = Path(model_path) if model_path else serving.CHECKPOINT_PATH
    if model_path.resolve() != serving.CHECKPOINT_PATH.resolve():
        raise ValueError('Checkpoint must match the selected verified release; use AURALIS_RELEASE=3.1 or 3.2')
    if device is None:
        device = torch.device('cpu') if serving.FIXED_CPU_EXECUTION else get_device()
    if serving.FIXED_CPU_EXECUTION:
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Checkpoint not found: {model_path}")

    logger.info("Loading checkpoint: %s", model_path)

    model = Coronium(in_channels=2, dropout_rate=serving.BACKBONE_DROPOUT)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
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
    """Run one forward pass and return the scalar prediction."""
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        prediction = model(image_tensor)

    predicted_index: float = prediction.item()
    logger.info("%s seed=%s: PyTorch deterministic eval (%s); SI=%.9f", serving.MODEL_NAME, serving.SEED, device, predicted_index)

    return predicted_index


def get_real_sunspot_index(
    filename: str,
    metadata_csv: str = "data/processed/metadata_processed.csv",
) -> Optional[float]:
    """Look up a sample's ground-truth index in the processed metadata CSV."""
    if not Path(metadata_csv).exists():
        logger.warning("Metadata CSV not found: %s", metadata_csv)
        return None

    metadata = pd.read_csv(metadata_csv)
    column = 'processed_file' if filename.endswith('.npy') else 'filename'
    match = metadata[metadata[column] == filename]

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
    output_path: Optional[str] = None,
) -> None:
    """Save a quick diagnostic magnetogram with prediction annotations."""
    output_path = output_path or f'reports/figures/coronium_v{serving.MODEL_VERSION.replace(chr(46), chr(95))}_prediction.png'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection=solar_map)

    norm = Normalize(vmin=-200, vmax=200)
    solar_map.plot(axes=ax, cmap="hmimag", norm=norm)
    solar_map.draw_grid(axes=ax, color="white", alpha=0.4, linewidth=0.5)

    obs_time = solar_map.date.utc.strftime("%Y-%m-%d %H:%M:%S")
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

    ax.set_title(serving.MODEL_NAME + " · PyTorch deterministic eval\n" + title, fontsize=11)

    cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.046, pad=0.08)
    cbar.set_label("LOS Magnetic Field (Gauss)", rotation=270, labelpad=25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info("Visualisation saved: %s", output_path)
    plt.close()


def main() -> None:
    """CLI entry point for single-image inference."""
    parser = argparse.ArgumentParser(
        description=(
            f"{serving.MODEL_NAME}: clip400 B+/B-; raw SI pixel-percent output; PyTorch deterministic eval."
        )
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Path to an HMI FITS or processed clip400 NPY. Defaults to the first FITS in data/raw/.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional exact selected-release checkpoint path; selection uses AURALIS_RELEASE.",
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
    if image_path.suffix.lower() == '.npy':
        image_tensor = torch.from_numpy(prepare_model_input(np.load(image_path, allow_pickle=False)))[None]
        solar_map = None
    else:
        image_tensor, solar_map = preprocess_fits_image(image_path)
    predicted_index = predict_sunspot_index(model, image_tensor, device)
    real_index = get_real_sunspot_index(image_path.name if image_path.suffix == '.npy' else image_path.stem)
    if solar_map is not None:
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
