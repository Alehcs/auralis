"""Training pipeline for the Coronium V3 PRO regressor.

Coronium predicts the current sunspot proxy index from dual-channel HMI
magnetograms. V3 PRO keeps the model small for local ONNX inference while adding
ECA attention and activity-weighted loss to reduce quiet-Sun bias.
"""

import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
import torchvision.transforms as transforms
from tqdm import tqdm
from sklearn.model_selection import train_test_split


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


class SolarAugmentation:
    """Standard stochastic augmentation for non-extreme training samples.

    Flips and small rotations preserve the visual morphology we need without
    changing the target index.
    """

    def __init__(self) -> None:
        self.transforms = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
        ])

    def __call__(self, img: torch.Tensor) -> torch.Tensor:
        """Apply the composed transforms to a single magnetogram tensor."""
        return self.transforms(img)


class ExtremeAugmentation:
    """Interpolation-free augmentation for high-activity solar magnetogram samples.

    High-index samples are rare and carry sharp polarity boundaries. This path
    uses only flips and 90-degree rotations so augmentation never interpolates
    or blurs those boundaries.
    """

    def __call__(self, img: torch.Tensor) -> torch.Tensor:
        """Apply stochastic isometric transforms without resampling pixels."""
        # Horizontal flip along the W axis (p=0.5)
        if torch.rand(1).item() > 0.5:
            img = torch.flip(img, dims=[2])

        # Vertical flip along the H axis (p=0.5)
        if torch.rand(1).item() > 0.5:
            img = torch.flip(img, dims=[1])

        # Rotation in {0°, 90°, 180°, 270°} — pixel-perfect, no interpolation
        k = int(torch.randint(0, 4, (1,)).item())
        if k > 0:
            img = torch.rot90(img, k=k, dims=[1, 2])

        return img


class SolarDataset(Dataset):
    """PyTorch Dataset wrapper for preprocessed dual-channel HMI magnetogram tensors.

    Current samples are `(2, H, W)` arrays with B+ and B- channels. Older
    single-channel arrays are converted at load time so historical datasets can
    still be inspected, but new training data should come from `prepare_dataset`.
    """

    def __init__(
        self,
        data_dir: str = "data/processed",
        metadata_csv: str = "data/processed/metadata_processed.csv",
        transform: Optional[SolarAugmentation] = None,
        extreme_threshold: Optional[float] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.extreme_threshold = extreme_threshold
        # Pre-instantiate only when threshold is active (never for val datasets).
        self._extreme_aug = ExtremeAugmentation() if extreme_threshold is not None else None
        self.metadata = pd.read_csv(metadata_csv)
        logger.info("Dataset loaded: %d samples", len(self.metadata))
        logger.info(
            "Sunspot index range: [%.3f, %.3f]",
            self.metadata["sunspot_index"].min(),
            self.metadata["sunspot_index"].max(),
        )
        if self.extreme_threshold is not None:
            n_extreme = int((self.metadata["sunspot_index"] > self.extreme_threshold).sum())
            logger.info(
                "ExtremeAugmentation active — threshold: %.1f  |  "
                "extreme samples: %d / %d (%.1f%%)",
                self.extreme_threshold, n_extreme, len(self.metadata),
                100.0 * n_extreme / len(self.metadata),
            )

    def __len__(self) -> int:
        return len(self.metadata)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Return one dual-channel tensor and its scalar sunspot-index target."""
        raw_filename: str = str(self.metadata.iloc[idx]["processed_file"])
        # Legacy rows have original_shape in processed_file due to a column
        # swap in an older version of prepare_dataset. Detect and reconstruct.
        if raw_filename.startswith("("):
            stem: str = str(self.metadata.iloc[idx]["filename"])
            filename = f"{stem}_processed.npy"
        else:
            filename = raw_filename
        image: np.ndarray = np.load(str(self.data_dir / filename))

        # V2-compatibility: single-channel (H, W) → dual-channel (2, H, W).
        # V2 normalisation is data/clip_value ∈ [-1, 1]; sign is preserved, so
        # ReLU(x) / ReLU(-x) gives the same polarity decomposition as V3 PRO.
        if image.ndim == 2:
            b_pos: np.ndarray = np.maximum(0.0, image)
            b_neg: np.ndarray = np.maximum(0.0, -image)
            image = np.stack([b_pos, b_neg], axis=0)  # (2, H, W)

        target: float = self.metadata.iloc[idx]["sunspot_index"]

        image_tensor: torch.Tensor = torch.from_numpy(image).float()
        target_tensor: torch.Tensor = torch.tensor([target], dtype=torch.float32)

        if (
            self._extreme_aug is not None          # threshold active (train only)
            and target > self.extreme_threshold    # sample is high-activity
        ):
            # Targeted augmentation: interpolation-free isometric transforms.
            # Replaces base SolarAugmentation to avoid bilinear artefacts on
            # the most informative (and rarest) high-index samples.
            image_tensor = self._extreme_aug(image_tensor)
        elif self.transform:
            # Standard augmentation for normal samples (existing behaviour).
            image_tensor = self.transform(image_tensor)

        return image_tensor, target_tensor


class WeightedHuberLoss(nn.Module):
    """Activity-aware Huber loss for solar magnetogram regression.

    The target distribution is quiet-Sun heavy, so plain MSE underweights the
    rare active-region cases. Huber caps outlier gradients, while `(1 + alpha*y)`
    gives higher-index samples more influence without oversampling.
    """

    def __init__(self, delta: float = 1.0, alpha: float = 2.0) -> None:
        super().__init__()
        self.delta = delta
        self.alpha = alpha

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        """Compute the mean weighted Huber loss over a batch."""
        return weighted_huber_loss(y_pred, y_true, delta=self.delta, alpha=self.alpha)


def weighted_huber_loss(
    y_pred: torch.Tensor,
    y: torch.Tensor,
    delta: float = 1.0,
    alpha: float = 2.0,
) -> torch.Tensor:
    """Activity-proportional Huber loss for solar dynamic-range regression.

    Formula: `mean((1 + alpha*y) * huber_delta(y_pred - y))`.
    """
    residual = y_pred - y
    abs_residual = residual.abs()

    huber = torch.where(
        abs_residual <= delta,
        0.5 * residual ** 2,
        delta * (abs_residual - 0.5 * delta),
    )
    weight = 1.0 + alpha * y
    return (weight * huber).mean()


class ECAAttention(nn.Module):
    """Lightweight channel attention via 1-D convolution (Wang et al., 2020).

    ECA captures local cross-channel dependencies with only a few parameters,
    which keeps attention affordable for the small ONNX target model.
    """

    def __init__(self, channels: int) -> None:
        super().__init__()
        k: int = max(3, 2 * (int(math.log2(channels)) // 2) + 1)  # always odd
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k, padding=k // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply channel attention weights to the input feature map."""
        y = self.avg_pool(x)                         # (N, C, 1, 1)
        y = y.squeeze(-1).transpose(-1, -2)          # (N, 1, C)
        y = self.conv(y)                             # (N, 1, C)
        y = y.transpose(-1, -2).unsqueeze(-1)        # (N, C, 1, 1)
        return x * self.sigmoid(y)


class V3ResidualBlock(nn.Module):
    """Residual block with ECA attention for Coronium V3 PRO.

    The skip projection only changes channel count; spatial structure is left
    to the main 3x3 convolution. Dropout2d regularizes whole feature maps and is
    also the source of MC Dropout uncertainty during validation.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        dropout_rate: float = 0.2,
    ) -> None:
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, kernel_size=3, padding=1, bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.eca = ECAAttention(out_channels)
        self.dropout = nn.Dropout2d(p=dropout_rate)

        self.skip = (
            nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels),
            )
            if in_channels != out_channels
            else nn.Identity()
        )
        self.out_relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply convolution, ECA attention, skip connection, and dropout."""
        main = self.eca(self.relu(self.bn(self.conv(x))))
        return self.dropout(self.out_relu(main + self.skip(x)))


class CoroniumV3(nn.Module):
    """Four-stage residual CNN promoted as the V3 PRO architecture.

    The 32/64/96/128 channel schedule is the model shape exported to ONNX. Global
    average pooling keeps parameter count low and makes the head independent of
    the input's final spatial size.
    """

    def __init__(self, in_channels: int = 2, dropout_rate: float = 0.2) -> None:
        super().__init__()

        # --- Backbone: four widened residual stages ----------------------------
        # Schedule: 32 → 64 → 96 → 128 (up from 16 → 32 → 64 → 96)
        self.stage1 = V3ResidualBlock(in_channels, 32, dropout_rate)   # 512→256
        self.pool1  = nn.MaxPool2d(kernel_size=2, stride=2)

        self.stage2 = V3ResidualBlock(32, 64, dropout_rate)            # 256→128
        self.pool2  = nn.MaxPool2d(kernel_size=2, stride=2)

        self.stage3 = V3ResidualBlock(64, 96, dropout_rate)            # 128→ 64
        self.pool3  = nn.MaxPool2d(kernel_size=2, stride=2)

        self.stage4 = V3ResidualBlock(96, 128, dropout_rate)           #  64→ 32
        self.pool4  = nn.MaxPool2d(kernel_size=2, stride=2)

        # --- Head: global pooling → dropout → regression ----------------------
        # AdaptiveAvgPool collapses (N, 128, 32, 32) → (N, 128, 1, 1),
        # avoiding parameter explosion from a raw Flatten.
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))

        # Scalar dropout regularises the 128-d descriptor before the linear
        # projection, complementing Dropout2d inside each residual block.
        self.head_dropout = nn.Dropout(p=0.3)

        # Final regression layer: 128 channels → 1 predicted sunspot index.
        self.fc = nn.Linear(128, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Compute predicted sunspot indices for a batch of B+/B- tensors."""
        # Backbone — four residual stages with spatial downsampling
        x = self.pool1(self.stage1(x))   # (N,  32, 256, 256)
        x = self.pool2(self.stage2(x))   # (N,  64, 128, 128)
        x = self.pool3(self.stage3(x))   # (N,  96,  64,  64)
        x = self.pool4(self.stage4(x))   # (N, 128,  32,  32)

        # Head — collapse spatial dims, regularise, regress
        x = self.global_avg_pool(x)      # (N, 128,   1,   1)
        x = x.view(x.size(0), -1)        # (N, 128)
        x = self.head_dropout(x)         # (N, 128) — scalar dropout
        return self.fc(x)                # (N,   1)


class EarlyStopping:
    """Stop training after repeated validation-loss stalls."""

    def __init__(self, patience: int = 10, min_delta: float = 0.0) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.counter: int = 0
        self.best_loss: Optional[float] = None
        self.early_stop: bool = False

    def __call__(self, val_loss: float) -> bool:
        """Return True once the configured patience has been exhausted."""
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

        return self.early_stop


def enable_mc_dropout(model: nn.Module) -> None:
    """Switch model to MC Dropout inference mode.

    Sets the model to eval mode (freezing BatchNorm running statistics) and
    then re-enables all Dropout and Dropout2d layers so that T stochastic
    forward passes produce an uncertainty estimate without corrupting BatchNorm
    running statistics.
    """
    model.eval()
    for module in model.modules():
        if isinstance(module, (nn.Dropout, nn.Dropout2d)):
            module.train()


def get_device() -> torch.device:
    """Select the best available compute backend for local training."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Using CUDA: %s", torch.cuda.get_device_name(0))
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using MPS (Apple Silicon)")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    return device


def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    criterion: WeightedHuberLoss,
    criterion_mae: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    """Execute one full pass over the training DataLoader.

    ``WeightedHuberLoss`` drives backpropagation. It combines Huber robustness
    (capping gradient magnitude for large residuals) with activity-proportional
    sample weighting, ensuring that rare high-activity observations receive
    proportionally more gradient signal. MAE is tracked only for reporting.
    """
    model.train()
    running_whl = 0.0
    running_mae = 0.0

    for images, targets in tqdm(train_loader, desc="Training", leave=False):
        images = images.to(device)
        targets = targets.to(device)

        outputs = model(images)
        loss_whl = criterion(outputs, targets)
        loss_mae = criterion_mae(outputs, targets)

        optimizer.zero_grad()
        loss_whl.backward()
        optimizer.step()

        running_whl += loss_whl.item()
        running_mae += loss_mae.item()

    n = len(train_loader)
    return running_whl / n, running_mae / n


def validate_epoch(
    model: nn.Module,
    val_loader: DataLoader,
    criterion: WeightedHuberLoss,
    criterion_mae: nn.Module,
    device: torch.device,
    mc_passes: int = 20,
) -> Tuple[float, float]:
    """Execute one full pass over the validation DataLoader with MC Dropout.

    MC Dropout is activated via ``enable_mc_dropout``: BatchNorm layers use
    frozen running statistics while Dropout2d layers remain stochastic.
    ``mc_passes`` independent forward passes are averaged per batch, providing
    an ensemble mean for the validation loss.
    """
    enable_mc_dropout(model)
    running_whl = 0.0
    running_mae = 0.0

    with torch.no_grad():
        for images, targets in tqdm(val_loader, desc="Validation (MC)", leave=False):
            images = images.to(device)
            targets = targets.to(device)

            # MC Dropout ensemble: T stochastic passes → mean prediction
            preds = torch.stack(
                [model(images) for _ in range(mc_passes)], dim=0
            )  # (T, N, 1)
            outputs = preds.mean(dim=0)  # (N, 1)

            running_whl += criterion(outputs, targets).item()
            running_mae += criterion_mae(outputs, targets).item()

    model.eval()  # restore clean eval mode after validation
    n = len(val_loader)
    return running_whl / n, running_mae / n


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 0.001,
    patience: int = 10,
    device: Optional[torch.device] = None,
) -> Dict[str, List[float]]:
    """Train CoroniumV3 with plateau scheduling, early stopping, and checkpointing."""
    if device is None:
        device = get_device()

    model = model.to(device)

    criterion = WeightedHuberLoss(delta=1.0, alpha=2.0)
    criterion_mae = nn.L1Loss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3, min_lr=1e-6
    )
    early_stopping = EarlyStopping(patience=patience)

    history: Dict[str, List[float]] = {
        "train_whl": [],
        "val_whl": [],
        "train_mae": [],
        "val_mae": [],
        "learning_rate": [],
    }

    logger.info("=" * 70)
    logger.info("Training CoroniumV3 PRO — dual-channel ECA residual")
    logger.info(
        "Max epochs: %d  |  Initial LR: %.4f  |  Early stopping patience: %d  |  Device: %s",
        num_epochs, learning_rate, patience, device,
    )
    logger.info("Loss: weighted_huber_loss  delta=1.0  alpha=2.0  |  Eval: MC Dropout T=20")
    logger.info("=" * 70)

    best_val_mae = float("inf")

    for epoch in range(1, num_epochs + 1):
        train_whl, train_mae = train_epoch(
            model, train_loader, criterion, criterion_mae, optimizer, device
        )
        val_whl, val_mae = validate_epoch(
            model, val_loader, criterion, criterion_mae, device
        )
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_whl"].append(train_whl)
        history["val_whl"].append(val_whl)
        history["train_mae"].append(train_mae)
        history["val_mae"].append(val_mae)
        history["learning_rate"].append(current_lr)

        logger.info(
            "Epoch %d/%d  |  Train WHL: %.6f  Val WHL: %.6f  |"
            "  Train MAE: %.4f  Val MAE: %.4f  |  LR: %.6f",
            epoch, num_epochs, train_whl, val_whl, train_mae, val_mae, current_lr,
        )

        # Save checkpoint on minimum val_mae (direct regression metric),
        # not val_whl — ensures the saved weights correspond to the best
        # generalisation in log-SI space rather than the loss landscape.
        if val_mae < best_val_mae:
            best_val_mae = val_mae
            Path("models").mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), "models/best_coronium_v3_pro_augmented.pth")
            logger.info(
                "Checkpoint saved  |  val_mae: %.4f  val_whl: %.6f", val_mae, val_whl
            )

        scheduler.step(val_whl)

        if early_stopping(val_whl):
            logger.info(
                "Early stopping at epoch %d — no improvement for %d consecutive epochs.",
                epoch, patience,
            )
            break

    logger.info("=" * 70)
    logger.info(
        "Training complete  |  Best val_mae: %.4f  |  Epochs: %d/%d",
        best_val_mae, len(history["train_whl"]), num_epochs,
    )
    logger.info("=" * 70)

    return history


def plot_learning_curve(
    history: Dict[str, List[float]],
    output_path: str = "reports/figures/learning_curve_v3_pro.png",
) -> None:
    """Persist loss, MAE, and learning-rate history as a diagnostic figure."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    epochs = range(1, len(history["train_whl"]) + 1)

    ax1.plot(epochs, history["train_whl"], "b-", label="Train WHL", linewidth=2)
    ax1.plot(epochs, history["val_whl"], "r-", label="Validation WHL", linewidth=2)
    ax1.set_title("Weighted Huber Loss (δ=1.0, α=2.0) — CoroniumV3 PRO  |  MC Dropout eval", fontsize=14)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Weighted Huber Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(epochs, history["train_mae"], "g-", label="Train MAE", linewidth=2)
    ax2.plot(epochs, history["val_mae"], color="orange", label="Validation MAE", linewidth=2)
    ax2.set_title("MAE (sunspot index units)", fontsize=14)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("MAE")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3.plot(epochs, history["learning_rate"], "m-", linewidth=2)
    ax3.set_title("Learning Rate Schedule", fontsize=14)
    ax3.set_xlabel("Epoch")
    ax3.set_ylabel("Learning Rate")
    ax3.set_yscale("log")
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info("Learning curve saved: %s", output_path)
    plt.close()


def main() -> None:
    """Execute the Coronium V3 PRO training pipeline."""
    BATCH_SIZE = 32
    NUM_EPOCHS = 100
    LEARNING_RATE = 0.001
    EARLY_STOPPING_PATIENCE = 10
    VAL_SPLIT = 0.2

    logger.info("Loading dataset...")

    train_dataset_full = SolarDataset(
        data_dir="data/processed",
        metadata_csv="data/processed/metadata_processed.csv",
        transform=SolarAugmentation(),
        extreme_threshold=2.0,    # targeted augmentation for high-activity samples
    )
    val_dataset_full = SolarDataset(
        data_dir="data/processed",
        metadata_csv="data/processed/metadata_processed.csv",
        transform=None,
        # extreme_threshold intentionally omitted (defaults to None):
        # double lock — both transform and _extreme_aug are disabled for val.
    )

    total_size = len(train_dataset_full)
    indices = list(range(total_size))

    # Shuffle prevents late-cycle extreme events from being concentrated in
    # validation, while random_state=42 keeps training and evaluation aligned.
    train_indices, val_indices = train_test_split(
        indices, test_size=VAL_SPLIT, shuffle=True, random_state=42
    )

    train_dataset = Subset(train_dataset_full, train_indices)
    val_dataset   = Subset(val_dataset_full,   val_indices)

    # Both splits must include high-activity events so validation reflects the
    # range the dashboard can surface.
    all_targets = train_dataset_full.metadata["sunspot_index"].values
    max_y_train = all_targets[train_indices].max()
    max_y_val   = all_targets[val_indices].max()
    logger.info("Split max y - train: %.4f  |  val: %.4f  (expected > 2.70)", max_y_train, max_y_val)
    assert max_y_train > 2.70, f"Train split has no extreme events: max_y={max_y_train:.4f}"
    assert max_y_val   > 2.70, f"Validation split has no extreme events: max_y={max_y_val:.4f}"

    # Persist split indices so evaluation scripts use the exact same hold-out set.
    import json as _json
    Path("models").mkdir(parents=True, exist_ok=True)
    split_path = Path("models/split_indices.json")
    with open(split_path, "w") as f:
        _json.dump({"train": train_indices, "val": val_indices, "random_state": 42}, f)
    logger.info("Split indices saved to %s", split_path)

    logger.info("Train: %d samples (augmentation enabled)", len(train_dataset))
    logger.info("Val:   %d samples (augmentation disabled)", len(val_dataset))

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = CoroniumV3(in_channels=2, dropout_rate=0.2)
    total_params = sum(p.numel() for p in model.parameters())
    assert total_params < 500_000, (
        f"CoroniumV3 parameter count {total_params:,} exceeds 500 K budget. "
        "Reduce filter counts or remove blocks."
    )
    logger.info(
        "CoroniumV3 PRO - %d parameters (~206,875 expected)  |  input: (2, 512, 512) [B+, B-]",
        total_params,
    )

    device = get_device()

    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        patience=EARLY_STOPPING_PATIENCE,
        device=device,
    )

    Path("models").mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), "models/coronium_v3_final.pth")
    logger.info("Final weights saved: models/coronium_v3_final.pth")

    plot_learning_curve(history)

    logger.info("Training pipeline complete.")


if __name__ == "__main__":
    main()
