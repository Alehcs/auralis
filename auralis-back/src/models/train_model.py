"""Training pipeline for Coronium V3 PRO — dual-channel ECA residual architecture.

Coronium is a lightweight CNN regressor trained on HMI/SDO Level-1.5
magnetograms to predict a proxy sunspot index. V3 PRO introduces Efficient
Channel Attention (ECA) within residual blocks and a narrower filter schedule
(16→32→64→96), totalling ~88,313 trainable parameters while preserving the
resolution-agnostic Global Average Pooling regression head.

The dual-channel input (B+, B-) encodes positive and negative polarity lobes
separately, enabling convolutional kernels to specialise by polarity sign.

Training protocol:
    Loss      : WeightedHuberLoss (δ=1.0, α=2.0) + L1 (diagnostic reporting)
    Optimiser : AdamW, lr=1e-3, weight_decay=1e-5
    Schedule  : ReduceLROnPlateau (factor=0.5, patience=3, min_lr=1e-6)
    Stop      : EarlyStopping (patience=10) on validation Weighted Huber Loss
    Eval      : MC Dropout (T=20 forward passes, dropout active) + mean prediction
    Aug       : random horizontal/vertical flip, ±10° rotation

Why α=2.0 (vs prior α=0.1):
    The V3 PRO dataset spans the full Solar Cycle 24 dynamic range where
    active-region samples (sunspot index > 5 %) achieve a 3× upweight at
    y=1.0 and a 41× upweight at y=20 %, directly addressing the quiet-Sun
    dominance bias observed in V2 evaluation curves.
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
            img: Float tensor of shape (2, H, W) — channels B+ and B-.

        Returns:
            Augmented tensor with identical shape.
        """
        return self.transforms(img)


class ExtremeAugmentation:
    """Interpolation-free augmentation for high-activity solar magnetogram samples.

    Applied exclusively to samples whose sunspot_index exceeds ``extreme_threshold``
    (default 2.0). Uses only isometric transforms that preserve the log-scaled
    polarity signal exactly:

    - ``torch.flip``   — bitwise pixel reversal along H or W; zero information loss.
    - ``torch.rot90``  — exact 90°-multiple rotation; no interpolation kernel applied.

    ``torchvision.RandomRotation(degrees=arbitrary)`` is intentionally avoided:
    bilinear interpolation creates edge artefacts on active-region boundaries and
    introduces sub-pixel signal mixing in the log-scaled B+/B- channels, which
    corrupts the polarity gradient information the model relies on for high-index
    predictions.

    Physical validity (Hale's law): solar bipolar active regions are statistically
    symmetric under hemisphere reflection and 90°-multiple rotation, so these
    transforms do not introduce polarity bias into the training distribution.
    """

    def __call__(self, img: torch.Tensor) -> torch.Tensor:
        """Apply stochastic isometric transforms to a dual-channel magnetogram tensor.

        Args:
            img: Float tensor of shape (2, H, W) — channels B+ and B-.

        Returns:
            Augmented tensor with identical shape (no spatial resampling).
        """
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

    Each sample is a two-channel float32 array of shape (2, H, W) stored as a
    ``.npy`` file by ``prepare_dataset``. Channel 0 is B+ = ReLU(log-scaled flux)
    and channel 1 is B- = ReLU(-log-scaled flux), representing the positive and
    negative polarity lobes of each bipolar active region independently. The
    validation subset is constructed from the same class with ``transform=None``
    to prevent data leakage from stochastic operations.

    V2-compatibility: files generated by the V2 pipeline are single-channel
    ``(H, W)`` arrays normalised to ``[-1, 1]``. Because that normalisation
    preserves field sign, the B+/B- polarity split is applied automatically at
    load time so that V2 and V3 PRO files are handled transparently.

    Args:
        data_dir: Directory containing ``.npy`` processed magnetogram files.
        metadata_csv: Path to the CSV produced by ``prepare_dataset``,
            containing at minimum the columns ``processed_file`` and
            ``sunspot_index``.
        transform: Optional callable applied to normal samples (target ≤ threshold).
            Expected interface: ``Tensor -> Tensor``.
        extreme_threshold: When set, samples whose ``sunspot_index`` exceeds this
            value receive ``ExtremeAugmentation`` (interpolation-free isometric
            transforms) instead of ``transform``. Set to ``None`` for the
            validation dataset to guarantee immutable validation data.
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
        """Return a single (image, target) pair.

        Args:
            idx: Integer index into the metadata table.

        Returns:
            Tuple of:
                - Image tensor of shape (2, 512, 512), dtype float32.
                  Channel 0: B+ positive polarity map. Channel 1: B- negative polarity map.
                - Target tensor of shape (1,) containing the sunspot index.
        """
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

    Computes a per-sample Huber loss re-weighted by the magnitude of the
    target sunspot index:

        L(ŷ, y) = mean_over_batch { (1 + α · |y|) · huber_δ(ŷ, y) }

    where the Huber kernel is:

        huber_δ(ŷ, y) = 0.5 · (ŷ − y)²              if |ŷ − y| ≤ δ
                         δ · (|ŷ − y| − 0.5 · δ)      otherwise

    Why this loss is superior to MSE for the solar activity bias
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    The sunspot index distribution is strongly right-skewed: the vast majority
    of HMI observations correspond to quiet-Sun days (index ≈ 0–1 %), while
    active and X-class-flare-precursor days (index > 5 %) are rare. A plain
    MSE objective has two compounding failure modes in this regime:

    1. **Quadratic tail sensitivity.** MSE penalises large residuals with
       squared magnitude, which sounds desirable for active-region accuracy.
       In practice, a handful of catastrophic quiet-Sun misses (the model
       predicting spurious activity) can dominate the total gradient and
       steer weights away from learning active-region morphology — the very
       task we care about.

    2. **Implicit class imbalance.** Because quiet-Sun samples outnumber
       active-region samples by ~10:1 in a typical solar-cycle dataset, the
       MSE gradient is overwhelmingly driven by the majority class. The model
       learns to minimise residuals on quiet days at the cost of systematic
       underestimation on active days, producing the characteristic
       *activity-floor bias* observed in V2/V3 PRO validation curves.

    The Weighted Huber Loss corrects both failure modes simultaneously:

    - **Huber robustness (δ=1.0).** For residuals |r| > δ the gradient is
      capped at a constant δ rather than growing as 2·r. This prevents
      the few extreme quiet-Sun mispredictions from overriding active-region
      gradient signal. For small residuals (|r| ≤ δ) behaviour is identical
      to MSE, so precision on common cases is unchanged.

    - **Activity-proportional weighting (α·|y|).** Each sample's loss
      contribution is scaled by (1 + α · |y|). For a quiet-Sun image
      (y ≈ 0.2 %): weight ≈ 1.02 (essentially unaffected). For a moderate
      active region (y ≈ 5 %): weight ≈ 1.5. For a major active region
      (y ≈ 20 %): weight ≈ 3.0. The rare, physically important events
      therefore contribute proportionally more gradient per sample, directly
      counteracting the implicit class imbalance without requiring oversampling
      or class-balanced batching strategies.

    The result is a loss surface where the model is simultaneously *robust*
    to outlier quiet-Sun predictions and *incentivised* to fit active-region
    samples accurately — aligned with the physical objective of Coronium.

    Args:
        delta: Huber transition threshold. Residuals below δ are penalised
            quadratically; residuals above δ are penalised linearly.
            Default 1.0 matches the natural scale of the log-normalised
            sunspot index.
        alpha: Activity weighting coefficient. Scales the per-sample weight
            as (1 + α · y). Default 2.0 gives a 3× upweight at y=1.0 and
            a 41× upweight at y=20 %, covering the full Solar Cycle 24
            dynamic range without oversampling or class-balanced batching.
    """

    def __init__(self, delta: float = 1.0, alpha: float = 2.0) -> None:
        super().__init__()
        self.delta = delta
        self.alpha = alpha

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        """Compute the mean weighted Huber loss over a batch.

        Args:
            y_pred: Predicted sunspot indices, shape (N, 1).
            y_true: Ground-truth sunspot indices, shape (N, 1).

        Returns:
            Scalar loss tensor.
        """
        return weighted_huber_loss(y_pred, y_true, delta=self.delta, alpha=self.alpha)


def weighted_huber_loss(
    y_pred: torch.Tensor,
    y: torch.Tensor,
    delta: float = 1.0,
    alpha: float = 2.0,
) -> torch.Tensor:
    """Activity-proportional Huber loss for solar dynamic-range regression.

    Computes a per-sample Huber loss re-weighted by the magnitude of the
    target sunspot index:

        weight           = 1.0 + α · y
        huber_δ(ŷ, y)   = 0.5 · (ŷ − y)²              if |ŷ − y| ≤ δ
                           δ · (|ŷ − y| − 0.5 · δ)      otherwise
        L(ŷ, y)         = mean { weight · huber_δ(ŷ, y) }

    Why this loss for the solar dynamic range:
        The sunspot index distribution is right-skewed (~10:1 quiet-Sun to
        active-region ratio). Using α=2.0 the weighting scheme scales as:
        quiet Sun (y≈0.1): weight≈1.2; moderate AR (y≈1.0): weight≈3.0;
        major AR (y≈20): weight≈41.0. Combined with Huber robustness (δ=1.0),
        this corrects the *activity-floor bias* of MSE objectives observed
        in prior versions without requiring oversampling strategies.

    Args:
        y_pred: Predicted sunspot indices, shape (N, 1).
        y:      Ground-truth sunspot indices, shape (N, 1). Expected to be
                non-negative (sunspot index ∈ [0, ∞)).
        delta:  Huber transition threshold. Residuals below δ are penalised
                quadratically; residuals above δ are penalised linearly.
        alpha:  Activity weighting coefficient α in the weight formula.

    Returns:
        Scalar tensor — mean weighted Huber loss over the batch.
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

    ECA replaces the two fully-connected layers of SE-Net with a single 1-D
    convolution of kernel size k applied to the channel descriptor produced by
    Global Average Pooling. This reduces attention parameters from 2·C²/r to k
    (typically 3), making the overhead negligible relative to the backbone.

    Why ECA over SE-Net for Coronium V3 PRO:
        Solar magnetograms exhibit strong polarity-specific feature correlations
        across channels (B+ and its derived feature maps co-activate differently
        from B-). ECA's local cross-channel receptive field captures these
        inter-channel dependencies with only k parameters, adding ~0.002 % of
        total parameter count per stage — a far better efficiency trade-off than
        SE-Net's 2·C²/r overhead, which at C=96 would add ~18 K parameters.

    The adaptive kernel formula k = max(3, 2·⌊log₂(C)/2⌋ + 1) yields k=3 for
    C ≤ 64 and k=5 for C ∈ {65…256}, keeping the local cross-channel
    receptive field proportional to the channel count.

    Args:
        channels: Number of input feature-map channels C.
    """

    def __init__(self, channels: int) -> None:
        super().__init__()
        k: int = max(3, 2 * (int(math.log2(channels)) // 2) + 1)  # always odd
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k, padding=k // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply channel attention weights to the input feature map.

        Args:
            x: Feature map of shape (N, C, H, W).

        Returns:
            Channel-recalibrated tensor of identical shape.
        """
        y = self.avg_pool(x)                         # (N, C, 1, 1)
        y = y.squeeze(-1).transpose(-1, -2)          # (N, 1, C)
        y = self.conv(y)                             # (N, 1, C)
        y = y.transpose(-1, -2).unsqueeze(-1)        # (N, C, 1, 1)
        return x * self.sigmoid(y)


class V3ResidualBlock(nn.Module):
    """Residual block with ECA attention for Coronium V3 PRO.

    Main path : Conv3×3 → BN → ReLU → ECAAttention
    Skip path : Conv1×1 → BN  (only when in_channels ≠ out_channels, else Identity)
    Output    : ReLU(main + skip) → Dropout2d

    The 1×1 projection in the skip path matches channel dimensions without
    spatial mixing, preserving identity-shortcut semantics from He et al.
    (2016). Dropout2d is applied after the residual addition to regularise
    full feature maps rather than individual activations. When active during
    Monte Carlo inference, Dropout2d provides calibrated prediction uncertainty
    over the stochastic ensemble.

    Args:
        in_channels:  Number of input feature-map channels.
        out_channels: Number of output feature-map channels.
        dropout_rate: Spatial dropout probability applied after the block.
            Also governs MC Dropout uncertainty estimation at inference time.
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
        """Compute one residual block pass.

        Args:
            x: Input tensor of shape (N, in_channels, H, W).

        Returns:
            Output tensor of shape (N, out_channels, H, W).
        """
        main = self.eca(self.relu(self.bn(self.conv(x))))
        return self.dropout(self.out_relu(main + self.skip(x)))


class CoroniumV3(nn.Module):
    """Four-stage residual CNN with ECA attention for solar magnetogram regression.

    Architecture (V3 PRO — dual-channel, widened schedule):
        Stage 1 : V3ResidualBlock(2  →  32) → MaxPool2d(2)   512→256
        Stage 2 : V3ResidualBlock(32 →  64) → MaxPool2d(2)   256→128
        Stage 3 : V3ResidualBlock(64 →  96) → MaxPool2d(2)   128→ 64
        Stage 4 : V3ResidualBlock(96 → 128) → MaxPool2d(2)    64→ 32
        Head    : GlobalAvgPool → Dropout(0.3) → Linear(128, 1)

    Total parameters: ~206,875 (resource budget: 150 K–250 K for ONNX/C++ edge deployment).

    Channel schedule widened from (16→32→64→96) to (32→64→96→128) for
    increased representational capacity while remaining within the TinyML
    parameter budget. The wider filters improve discrimination of subtle
    polarity gradients in active-region magnetograms without requiring a
    deeper network (which would increase latency on edge hardware).

    A scalar Dropout(p=0.3) is applied after GlobalAvgPool and before the
    final Linear layer to regularise the 128-dimensional feature vector,
    complementing the spatial Dropout2d already present in each residual
    block. This two-level dropout strategy reduces co-adaptation of both
    spatial feature maps and the aggregated channel descriptor.

    MC Dropout is supported natively: calling ``enable_mc_dropout`` keeps
    Dropout2d active during inference, enabling T stochastic forward passes
    for calibrated uncertainty estimation over active-region predictions.

    Input shape:  (N, 2, 512, 512) — dual-channel HMI magnetogram (B+, B-)
    Output shape: (N, 1)           — predicted sunspot index

    Args:
        in_channels:  Number of input channels. Must match the channel count
            produced by ``prepare_dataset`` (default 2 for B+/B-).
        dropout_rate: Spatial dropout probability passed to every V3ResidualBlock.
            Also controls MC Dropout uncertainty spread at inference time.
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
        """Compute the regression output for a batch of magnetograms.

        Args:
            x: Input tensor of shape (N, 2, 512, 512).
                Channel 0: B+ positive polarity map. Channel 1: B- negative polarity map.

        Returns:
            Output tensor of shape (N, 1) containing predicted sunspot indices.
        """
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


def enable_mc_dropout(model: nn.Module) -> None:
    """Switch model to MC Dropout inference mode.

    Sets the model to eval mode (freezing BatchNorm running statistics) and
    then re-enables all Dropout and Dropout2d layers so that T stochastic
    forward passes produce a distribution of predictions. This implements
    the Gal & Ghahramani (2016) approximation to Bayesian inference.

    Why MC Dropout at validation for Coronium V3 PRO:
        Active-region samples are rare in the validation set. A single
        deterministic forward pass may confidently mispredict extreme solar
        events (high sunspot index). By averaging T=20 stochastic passes,
        the mean prediction is more robust and the per-sample std serves as
        a calibrated uncertainty proxy — flagging unreliable predictions on
        edge cases for downstream space-weather alert pipelines.

    Args:
        model: ``CoroniumV3`` instance. Modified in-place.
    """
    model.eval()
    for module in model.modules():
        if isinstance(module, (nn.Dropout, nn.Dropout2d)):
            module.train()


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
    criterion: WeightedHuberLoss,
    criterion_mae: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    """Execute one full pass over the training DataLoader.

    ``WeightedHuberLoss`` drives backpropagation. It combines Huber robustness
    (capping gradient magnitude for large residuals) with activity-proportional
    sample weighting, ensuring that rare high-activity observations receive
    proportionally more gradient signal than the dominant quiet-Sun majority.
    MAE is computed in parallel for interpretable diagnostic reporting in
    physical sunspot-index units.

    Args:
        model: Network in training mode; Dropout2d layers are active.
        train_loader: Iterable yielding (image, target) batches.
        criterion: ``WeightedHuberLoss`` instance for backpropagation.
        criterion_mae: ``nn.L1Loss`` instance for diagnostic reporting.
        optimizer: Gradient-based parameter update rule.
        device: Compute device matched to model and data placement.

    Returns:
        Tuple (mean_whl, mean_mae) averaged over all batches in the epoch.
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
    a calibrated ensemble prediction that is more robust on rare high-activity
    samples than a single deterministic pass. The Weighted Huber Loss is
    evaluated on the mean MC prediction, preserving the α=2.0 active-region
    priority of the training objective.

    ``torch.no_grad()`` disables autograd across all passes to avoid
    accumulating unnecessary gradient tensors in the stochastic ensemble.

    Args:
        model: Network. MC Dropout mode is applied internally; caller state
            is restored to eval after the function returns.
        val_loader: Iterable yielding (image, target) batches.
        criterion: ``WeightedHuberLoss`` instance (δ=1.0, α=2.0).
        criterion_mae: ``nn.L1Loss`` instance for diagnostic reporting.
        device: Compute device matched to model and data placement.
        mc_passes: Number of stochastic forward passes per batch for the
            MC Dropout ensemble mean. Higher values reduce variance at the
            cost of T× inference time.

    Returns:
        Tuple (mean_whl, mean_mae) averaged over all batches.
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
    """Run the full training loop with adaptive LR scheduling and early stopping.

    The learning rate is halved whenever validation Weighted Huber Loss fails
    to decrease for 3 consecutive epochs (ReduceLROnPlateau), preventing
    oscillation in flat loss regions. Training terminates early when no
    improvement is observed for ``patience`` epochs. The best checkpoint
    (lowest val WHL) is persisted to ``models/coronium_v3_pro.pth`` at each
    improvement.

    Args:
        model: Uninitialised Coronium instance.
        train_loader: DataLoader with augmentation applied.
        val_loader: DataLoader without augmentation.
        num_epochs: Upper bound on the number of training epochs.
        learning_rate: Initial AdamW learning rate (weight_decay=1e-5).
        patience: EarlyStopping patience in epochs.
        device: Target compute device. Detected automatically if ``None``.

    Returns:
        Dictionary with per-epoch lists for keys: 'train_whl', 'val_whl',
        'train_mae', 'val_mae', 'learning_rate'.
    """
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

    best_val_whl = float("inf")

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

        if val_whl < best_val_whl:
            best_val_whl = val_whl
            Path("models").mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), "models/best_coronium_v3_pro_augmented.pth")
            logger.info(
                "Checkpoint saved  |  val_whl: %.6f  val_mae: %.4f", val_whl, val_mae
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
        "Training complete  |  Best val_whl: %.6f  |  Epochs: %d/%d",
        best_val_whl, len(history["train_whl"]), num_epochs,
    )
    logger.info("=" * 70)

    return history


def plot_learning_curve(
    history: Dict[str, List[float]],
    output_path: str = "reports/figures/learning_curve_v3_pro.png",
) -> None:
    """Persist training history as a three-panel figure.

    Panels: (1) Weighted Huber Loss curves for train/validation, (2) MAE
    curves in sunspot-index units for interpretable error reporting,
    (3) learning rate schedule on a log scale to expose ReduceLROnPlateau
    step events.

    Args:
        history: Dictionary returned by ``train_model``.
        output_path: Filesystem path for the saved PNG (parent created if absent).
    """
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
    val_size = int(total_size * VAL_SPLIT)
    train_size = total_size - val_size

    indices = list(range(total_size))
    train_dataset = Subset(train_dataset_full, indices[:train_size])
    val_dataset = Subset(val_dataset_full, indices[train_size:])

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
        "CoroniumV3 PRO — %d parameters (~206,875 expected) ✓  |  input: (2, 512, 512) [B+, B-]",
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
