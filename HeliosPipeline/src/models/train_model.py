"""Training pipeline for SolarNet V2 PRO.

SolarNet is a lightweight CNN regressor trained on HMI/SDO Level-1.5
magnetograms to predict a proxy sunspot index. The architecture replaces the
fixed-size dense head used in VGG-style networks with Global Average Pooling,
making the regression head resolution-agnostic and reducing the total parameter
count to ~389 K — approximately 4.2% of an equivalent VGG-11 backbone.

Training protocol:
    Loss      : MSE (backpropagation) + L1 (diagnostic reporting)
    Optimiser : Adam, lr=1e-3
    Schedule  : ReduceLROnPlateau (factor=0.5, patience=5)
    Stop      : EarlyStopping (patience=10) on validation MSE
    Aug       : random horizontal/vertical flip, ±10° rotation
"""

import logging
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


class SolarAugmentation:
    """Stochastic augmentation pipeline for HMI magnetogram tensors.

    Random horizontal and vertical flips are valid because HMI Level-1.5 data
    has statistically symmetric polarity distributions across the equatorial
    plane (Hale's law), so hemisphere flips do not introduce polarity bias.
    Rotation is capped at ±10° to remain within the residual roll-angle
    uncertainty of the HMI instrument after P-angle correction upstream.
    """

    def __init__(self) -> None:
        self.transforms = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
        ])

    def __call__(self, img: torch.Tensor) -> torch.Tensor:
        """Apply the composed transforms to a single magnetogram tensor.

        Args:
            img: Float tensor of shape (1, H, W).

        Returns:
            Augmented tensor with identical shape.
        """
        return self.transforms(img)


class SolarDataset(Dataset):
    """PyTorch Dataset wrapper for preprocessed HMI magnetogram tensors.

    Each sample is a single-channel float32 array stored as a ``.npy`` file
    alongside a scalar sunspot index in the companion CSV. The dataset supports
    optional augmentation transforms applied only during training; the
    validation subset is constructed from the same class with
    ``transform=None`` to prevent data leakage from stochastic operations.

    Args:
        data_dir: Directory containing ``.npy`` processed magnetogram files.
        metadata_csv: Path to the CSV produced by ``prepare_dataset``,
            containing at minimum the columns ``processed_file`` and
            ``sunspot_index``.
        transform: Optional callable applied to the image tensor after loading.
            Expected interface: ``Tensor -> Tensor``.
    """

    def __init__(
        self,
        data_dir: str = "data/processed",
        metadata_csv: str = "data/processed/metadata_processed.csv",
        transform: Optional[SolarAugmentation] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.metadata = pd.read_csv(metadata_csv)
        logger.info("Dataset loaded: %d samples", len(self.metadata))
        logger.info(
            "Sunspot index range: [%.3f, %.3f]",
            self.metadata["sunspot_index"].min(),
            self.metadata["sunspot_index"].max(),
        )

    def __len__(self) -> int:
        return len(self.metadata)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Return a single (image, target) pair.

        Args:
            idx: Integer index into the metadata table.

        Returns:
            Tuple of:
                - Image tensor of shape (1, 512, 512), dtype float32.
                - Target tensor of shape (1,) containing the sunspot index.
        """
        filename = self.metadata.iloc[idx]["processed_file"]
        image = np.load(str(self.data_dir / filename))
        target = self.metadata.iloc[idx]["sunspot_index"]

        image = torch.from_numpy(image).float().unsqueeze(0)
        target = torch.tensor([target], dtype=torch.float32)

        if self.transform:
            image = self.transform(image)

        return image, target


class SolarNet(nn.Module):
    """Four-block CNN regressor for solar magnetogram analysis.

    Architecture rationale:
        Four Conv2d blocks progressively double the channel count
        (32→64→128→256) while halving spatial resolution via MaxPool2d(2,2),
        following a standard feature-hierarchy schedule. Dropout2d drops
        entire feature maps rather than individual activations, preventing
        co-adaptation of spatially-correlated filters.

        Global Average Pooling collapses each of the 256 feature maps to a
        scalar by averaging over all spatial positions. This eliminates
        O(H·W·C) parameters from the dense head, yielding a ~24× parameter
        reduction versus VGG-11 while preserving spatial invariance across
        the full solar disk. A single Linear(256, 1) layer produces the
        regression output.

    Input shape:  (N, 1, 512, 512) — normalised HMI LOS magnetogram
    Output shape: (N, 1)           — predicted sunspot index

    Args:
        dropout_rate: Channel-wise drop probability for Dropout2d layers.
    """

    def __init__(self, dropout_rate: float = 0.3) -> None:
        super().__init__()

        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout1 = nn.Dropout2d(p=dropout_rate)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout2 = nn.Dropout2d(p=dropout_rate)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout3 = nn.Dropout2d(p=dropout_rate)

        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout4 = nn.Dropout2d(p=dropout_rate)

        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, 1)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Compute the regression output for a batch of magnetograms.

        Args:
            x: Input tensor of shape (N, 1, 512, 512).

        Returns:
            Output tensor of shape (N, 1) containing predicted sunspot indices.
        """
        x = self.dropout1(self.pool1(self.relu(self.bn1(self.conv1(x)))))
        x = self.dropout2(self.pool2(self.relu(self.bn2(self.conv2(x)))))
        x = self.dropout3(self.pool3(self.relu(self.bn3(self.conv3(x)))))
        x = self.dropout4(self.pool4(self.relu(self.bn4(self.conv4(x)))))
        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


class EarlyStopping:
    """Halt training when validation loss shows no monotonic improvement.

    The counter increments whenever the current validation loss fails to
    improve by at least ``min_delta`` over the historical minimum. This
    prevents unnecessary compute on epochs that no longer reduce
    generalisation error.

    Args:
        patience: Number of non-improving epochs before triggering a stop.
        min_delta: Minimum absolute decrease in loss to count as improvement.
    """

    def __init__(self, patience: int = 10, min_delta: float = 0.0) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.counter: int = 0
        self.best_loss: Optional[float] = None
        self.early_stop: bool = False

    def __call__(self, val_loss: float) -> bool:
        """Evaluate the stopping criterion for the current epoch.

        Args:
            val_loss: Validation loss at the end of the current epoch.

        Returns:
            ``True`` if training should stop, ``False`` otherwise.
        """
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


def get_device() -> torch.device:
    """Select the highest-throughput available compute backend.

    CUDA is checked before MPS because NVIDIA data-centre GPUs generally
    offer higher memory bandwidth for the batch sizes used in training.
    MPS (Apple Silicon) is the preferred fallback for local development.

    Returns:
        ``torch.device`` pointing to the selected backend.
    """
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
    criterion_mse: nn.Module,
    criterion_mae: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    """Execute one full pass over the training DataLoader.

    MSE drives backpropagation because it penalises large prediction errors
    quadratically, discouraging the model from ignoring active-region outliers.
    L1 (MAE) is computed in parallel for diagnostic reporting in units of
    the sunspot index, which is physically interpretable.

    Args:
        model: Network in training mode; Dropout2d layers are active.
        train_loader: Iterable yielding (image, target) batches.
        criterion_mse: ``nn.MSELoss`` instance for backpropagation.
        criterion_mae: ``nn.L1Loss`` instance for reporting.
        optimizer: Gradient-based parameter update rule.
        device: Compute device matched to model and data placement.

    Returns:
        Tuple (mean_mse, mean_mae) averaged over all batches in the epoch.
    """
    model.train()
    running_mse = 0.0
    running_mae = 0.0

    for images, targets in tqdm(train_loader, desc="Training", leave=False):
        images = images.to(device)
        targets = targets.to(device)

        outputs = model(images)
        loss_mse = criterion_mse(outputs, targets)
        loss_mae = criterion_mae(outputs, targets)

        optimizer.zero_grad()
        loss_mse.backward()
        optimizer.step()

        running_mse += loss_mse.item()
        running_mae += loss_mae.item()

    n = len(train_loader)
    return running_mse / n, running_mae / n


def validate_epoch(
    model: nn.Module,
    val_loader: DataLoader,
    criterion_mse: nn.Module,
    criterion_mae: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    """Execute one full pass over the validation DataLoader.

    ``torch.no_grad()`` disables autograd to reduce peak memory consumption
    and avoid computing unnecessary gradient tensors during evaluation.
    BatchNorm layers use running statistics accumulated during training;
    Dropout2d is inactive.

    Args:
        model: Network in eval mode.
        val_loader: Iterable yielding (image, target) batches.
        criterion_mse: ``nn.MSELoss`` instance.
        criterion_mae: ``nn.L1Loss`` instance.
        device: Compute device matched to model and data placement.

    Returns:
        Tuple (mean_mse, mean_mae) averaged over all batches.
    """
    model.eval()
    running_mse = 0.0
    running_mae = 0.0

    with torch.no_grad():
        for images, targets in tqdm(val_loader, desc="Validation", leave=False):
            images = images.to(device)
            targets = targets.to(device)

            outputs = model(images)
            running_mse += criterion_mse(outputs, targets).item()
            running_mae += criterion_mae(outputs, targets).item()

    n = len(val_loader)
    return running_mse / n, running_mae / n


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 0.001,
    patience: int = 10,
    device: Optional[torch.device] = None,
) -> Dict[str, List[float]]:
    """Run the full training loop with adaptive LR scheduling and early stopping.

    The learning rate is halved whenever validation MSE fails to decrease for
    five consecutive epochs (ReduceLROnPlateau), preventing oscillation in
    flat loss regions. Training terminates early when no improvement is
    observed for ``patience`` epochs. The best checkpoint (lowest val MSE)
    is persisted to ``models/helios_v2_pro.pth`` at each improvement.

    Args:
        model: Uninitialised SolarNet instance.
        train_loader: DataLoader with augmentation applied.
        val_loader: DataLoader without augmentation.
        num_epochs: Upper bound on the number of training epochs.
        learning_rate: Initial Adam learning rate.
        patience: EarlyStopping patience in epochs.
        device: Target compute device. Detected automatically if ``None``.

    Returns:
        Dictionary with per-epoch lists for keys: 'train_mse', 'val_mse',
        'train_mae', 'val_mae', 'learning_rate'.
    """
    if device is None:
        device = get_device()

    model = model.to(device)

    criterion_mse = nn.MSELoss()
    criterion_mae = nn.L1Loss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )
    early_stopping = EarlyStopping(patience=patience)

    history: Dict[str, List[float]] = {
        "train_mse": [],
        "val_mse": [],
        "train_mae": [],
        "val_mae": [],
        "learning_rate": [],
    }

    logger.info("=" * 70)
    logger.info("Training SolarNet V2 PRO")
    logger.info(
        "Max epochs: %d  |  Initial LR: %.4f  |  Early stopping patience: %d  |  Device: %s",
        num_epochs, learning_rate, patience, device,
    )
    logger.info("=" * 70)

    best_val_mse = float("inf")

    for epoch in range(1, num_epochs + 1):
        train_mse, train_mae = train_epoch(
            model, train_loader, criterion_mse, criterion_mae, optimizer, device
        )
        val_mse, val_mae = validate_epoch(
            model, val_loader, criterion_mse, criterion_mae, device
        )
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_mse"].append(train_mse)
        history["val_mse"].append(val_mse)
        history["train_mae"].append(train_mae)
        history["val_mae"].append(val_mae)
        history["learning_rate"].append(current_lr)

        logger.info(
            "Epoch %d/%d  |  Train MSE: %.6f  Val MSE: %.6f  |"
            "  Train MAE: %.4f  Val MAE: %.4f  |  LR: %.6f",
            epoch, num_epochs, train_mse, val_mse, train_mae, val_mae, current_lr,
        )

        if val_mse < best_val_mse:
            best_val_mse = val_mse
            Path("models").mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), "models/helios_v2_pro.pth")
            logger.info(
                "Checkpoint saved  |  val_mse: %.6f  val_mae: %.4f", val_mse, val_mae
            )

        scheduler.step(val_mse)

        if early_stopping(val_mse):
            logger.info(
                "Early stopping at epoch %d — no improvement for %d consecutive epochs.",
                epoch, patience,
            )
            break

    logger.info("=" * 70)
    logger.info(
        "Training complete  |  Best val_mse: %.6f  |  Epochs: %d/%d",
        best_val_mse, len(history["train_mse"]), num_epochs,
    )
    logger.info("=" * 70)

    return history


def plot_learning_curve(
    history: Dict[str, List[float]],
    output_path: str = "reports/figures/learning_curve_v2_pro.png",
) -> None:
    """Persist training history as a three-panel figure.

    Panels: (1) MSE loss curves for train/validation, (2) MAE curves in
    sunspot-index units, (3) learning rate schedule on a log scale to expose
    ReduceLROnPlateau step events.

    Args:
        history: Dictionary returned by ``train_model``.
        output_path: Filesystem path for the saved PNG (parent created if absent).
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    epochs = range(1, len(history["train_mse"]) + 1)

    ax1.plot(epochs, history["train_mse"], "b-", label="Train MSE", linewidth=2)
    ax1.plot(epochs, history["val_mse"], "r-", label="Validation MSE", linewidth=2)
    ax1.set_title("MSE Loss — SolarNet V2 PRO", fontsize=14)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("MSE")
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
    """Execute the SolarNet V2 PRO training pipeline."""
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
    )
    val_dataset_full = SolarDataset(
        data_dir="data/processed",
        metadata_csv="data/processed/metadata_processed.csv",
        transform=None,
    )

    total_size = len(train_dataset_full)
    val_size = int(total_size * VAL_SPLIT)
    train_size = total_size - val_size

    indices = list(range(total_size))
    train_dataset = Subset(train_dataset_full, indices[:train_size])
    val_dataset = Subset(val_dataset_full, indices[train_size:])

    logger.info("Train: %d samples (augmentation enabled)", len(train_dataset))
    logger.info("Val:   %d samples (augmentation disabled)", len(val_dataset))

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = SolarNet(dropout_rate=0.3)
    total_params = sum(p.numel() for p in model.parameters())
    logger.info("SolarNet V2 PRO — %d parameters", total_params)

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
    torch.save(model.state_dict(), "models/helios_v2_final.pth")
    logger.info("Final weights saved: models/helios_v2_final.pth")

    plot_learning_curve(history)

    logger.info("Training pipeline complete.")


if __name__ == "__main__":
    main()
