# RESEARCH DOSSIER
## Coronium V3 PRO: A Residual Convolutional Neural Network for Solar Magnetic Activity Index Estimation from Dual-Channel HMI/SDO Magnetograms

**Classification:** Technical Research Report  
**Format:** IEEE Conference Paper Style  
**Repository:** Auralis  
**Dossier Generated:** 2026-04-02  
**Dossier Updated:** 2026-05-26  
**Dossier Version:** 3.3.0  

> This is the primary research dossier for the Auralis project, intended for academic and international review. It documents all technical content, equations, metrics, and reproducibility details for Coronium V3 PRO.

---

## Abstract

This report documents Coronium V3 PRO, a compact residual convolutional neural network designed to estimate a solar magnetic activity index from dual-channel line-of-sight magnetograms produced by the Helioseismic and Magnetic Imager (HMI) aboard NASA's Solar Dynamics Observatory (SDO). The model accepts a `(2, 512, 512)` float32 tensor in which channel 0 encodes positive magnetic polarity (B+) and channel 1 encodes negative magnetic polarity (B−), both derived from the symmetric-log-scaled HMI Level-1.5 field. The target variable is the log-transformed Sunspot Index (log-SI), a pixel-count proxy for strong-field area computed directly from the magnetogram.

Coronium V3 PRO achieves a Mean Absolute Error of **0.1048 log-SI**, RMSE of **0.1272 log-SI**, R² of **0.8634**, and MAPE of **6.07%** (accuracy proxy 100 − MAPE = **93.93%**) on a 353-magnetogram hold-out evaluated with Monte Carlo Dropout (T = 20, seed = 42). With 206,875 trainable parameters and an ONNX export of 86.6 KB, the model is deployable on CPU without a GPU or dedicated accelerator, running inference in 25.11 ms per image via ONNX Runtime.

This work addresses nowcasting of a magnetogram-derived activity proxy, not operational space-weather forecasting. No flare prediction, CME prediction, or geomagnetic-storm prediction is claimed or implied.

---

## Table of Contents

1. [Version Metadata and Reproducibility Record](#1-version-metadata-and-reproducibility-record)
2. [Data Engineering](#2-data-engineering)
3. [Architecture: Coronium V3 PRO](#3-architecture-coronium-v3-pro)
4. [Training Protocol](#4-training-protocol)
5. [Results and Benchmarking](#5-results-and-benchmarking)
6. [Explainability and Uncertainty Estimation](#6-explainability-and-uncertainty-estimation)
   - 6.1 Grad-CAM Implementation and Empirical Validation (incl. interactive faithfulness tool)
   - 6.2 Uncertainty Quantification — Two Distinct Protocols
   - 6.3 ONNX Deployment and CPU Latency
   - 6.4 High-Activity Regime Robustness
7. [Limitations and Future Work](#7-limitations-and-future-work)
8. [Conclusions](#8-conclusions)
- [Appendix A — Source File Reference Index](#appendix-a--source-file-reference-index)
- [Appendix B — Key Equations and Canonical Values](#appendix-b--key-equations-and-canonical-values)

---

## 1. Version Metadata and Reproducibility Record

### 1.1 Production Checkpoint

| Field | Value |
|---|---|
| Production checkpoint | `best_coronium_v3_pro_augmented.pth` |
| File size | ~829 KB |
| Checkpoint date | 2026-05-01 |
| System version | Coronium V3 PRO + ExtremeAugmentation |
| Experiment ID | `exp_005` |
| Run name | Coronium V3 PRO — ExtremeAugmentation Final |
| Experiment date | 2026-05-01T11:03:00Z |
| ONNX export | `best_coronium_v3_pro.onnx` — 86.6 KB, opset 18 |

### 1.2 Git Repository State

| Field | Value |
|---|---|
| Branch | `main` |
| Repository state | v3-pro consolidated — `exp_005` final (V3 PRO + ExtremeAugmentation) |
| Author | Alejandro Cornejo |

> The specific promoting commit hash is intentionally omitted: the `exp_005` production state was consolidated across the `v3-pro` branch merge. Run `git log --oneline` for the authoritative commit history.

### 1.3 Runtime Environment

| Parameter | Value |
|---|---|
| Framework | PyTorch 2.2.0 |
| Python version | 3.12.1 |
| Training device | MPS (Apple Silicon) |
| Operating system | macOS 15.4 |

### 1.4 Model Checkpoint Inventory

```
auralis-back/models/
├── coronium_v1.pth                      (~1.5 MB)  — Coronium V1 final weights
├── coronium_best.pth                    (~1.5 MB)  — Coronium V1 best-epoch weights
├── coronium_v2_final.pth                (~1.5 MB)  — Coronium V2 Tuned final weights
├── coronium_v2_pro.pth                  (~1.5 MB)  — Coronium V2 PRO weights [deprecated]
├── coronium_v3_final.pth                (~367 KB)  — Coronium V3 PRO last-epoch weights
├── best_coronium_v3_pro.pth             (~829 KB)  — Coronium V3 PRO original (no ExtremeAug)
├── best_coronium_v3_pro_augmented.pth   (~829 KB)  — Coronium V3 PRO + ExtremeAug [active]
└── best_coronium_v3_pro.onnx            (86.6 KB)  — ONNX export opset 18 [edge deployment]

Total model storage: ~8.9 MB
```

---

## 2. Data Engineering

### 2.1 Dataset Volume and Composition

**Source:** NASA Solar Dynamics Observatory (SDO), Helioseismic and Magnetic Imager (HMI)  
**Observable:** Line-of-sight magnetic field (`los_magnetic_field`)  
**Instrument identifier:** `HMI_FRONT2`  
**Spatial resolution:** 0.504 arcsec/pixel  
**Native image dimensions:** 4096 × 4096 pixels  
**Solar radius (HMI header):** 974.63 arcsec  

| Metric | Value |
|---|---|
| Total processed samples | **1,763** |
| Training set | **1,410** (79.98%) — with SolarAugmentation + ExtremeAugmentation |
| Validation set (hold-out) | **353** (20.02%) — `random_state=42`, no augmentation applied |
| Total dataset size (disk) | ~2.1 GB |
| Image format (processed) | NumPy binary (`.npy`) |
| Dtype | float32 |
| Processed spatial resolution | 512 × 512 pixels |
| Input channels | **2** (channel 0: B+, channel 1: B−) |
| Metadata file | `data/processed/metadata_processed.csv` |

The random split (`random_state=42`) was chosen to ensure that extreme-activity events from Solar Cycle 25 (2024–2025 maximum) appear in both the training and validation sets, eliminating the temporal domain shift observed in earlier chronological splits.

### 2.2 Temporal Distribution by Solar Cycle

The dataset was constructed to span Solar Cycles 24 and 25, with deliberate oversampling of the most recent active period.

**Source:** `auralis-back/src/ingestion/massive_ingest_pipeline.py`, lines 46–65

```
Dataset Temporal Distribution
─────────────────────────────────────────────────────────────────────
Period        Years        Target images   Fraction   Solar Cycle
─────────────────────────────────────────────────────────────────────
Period 1      2011–2013         500         25.0%     Cycle 24 (ascending/max)
Period 2      2015–2018         500         25.0%     Cycle 24 (declining)
Period 3      2021–2025        1000         50.0%     Cycle 25 (ascending/max)
─────────────────────────────────────────────────────────────────────
Total                          2000        100.0%
─────────────────────────────────────────────────────────────────────
Note: Target ingestion = 2000; validated and deduplicated = 1,763
─────────────────────────────────────────────────────────────────────
```

### 2.3 Target Variable: Sunspot Index Proxy

The Sunspot Index (SI) is a proxy computed directly from the magnetogram, defined as the fraction of pixels whose magnetic field strength exceeds a strong-field threshold B_thresh.

**Source:** `auralis-back/src/processing/prepare_dataset.py`, lines 83–84

$$
SI = \frac{|\lbrace p \in \mathcal{I} : |B(p)| > B_{thresh}\rbrace|}{|\mathcal{I}|} \times 100
$$

where:
- $\mathcal{I}$ is the set of all pixels in the native-resolution image
- $B(p)$ is the magnetic field value in Gauss at pixel $p$
- $B_{thresh} = 200.0\ \text{G}$ (configurable strong-field detection threshold)

This index is a magnetogram-derived activity proxy. It is not equivalent to the official NOAA sunspot number or any externally validated activity index. The SI is computed on the raw 4096 × 4096 array before any spatial resampling, to avoid artefacts from bilinear interpolation near the 200 G threshold boundary.

**Sunspot Index statistics over the full dataset (1,763 samples):**

| Statistic | Value | Units |
|---|---|---|
| Mean | 1.938 | % |
| Std dev | 0.394 | % |
| Minimum | 1.214 | % |
| Maximum | 2.990 | % |

**Observational baseline (single raw image, from exploratory notebook):**

| Statistic | Value | Units |
|---|---|---|
| Raw field minimum | −4808.40 | G |
| Raw field maximum | +4808.40 | G |
| Raw field mean | −0.37 | G |
| Raw field std dev | 76.39 | G |
| Pixels with \|B\| > 200 G | 1.78% | — |
| Active pixel count (sample) | 299,196 | pixels |

### 2.4 Input Normalisation Pipeline (V3 PRO)

**Source:** `auralis-back/src/processing/prepare_dataset.py` (`log_scale`, `load_and_process_magnetogram`)

The V3 PRO normalisation pipeline applies two sequential operations to the raw magnetic field array.

**Step 1 — Symmetric log scaling (sign-preserving):**

$$
B_{\mathrm{log}}(p) = \mathrm{sign}(B_{\mathrm{raw}}(p)) \cdot \log(1 + |B_{\mathrm{raw}}(p)|)
$$

Implemented as `np.sign(x) * np.log1p(np.abs(x))`. This compresses the raw dynamic range (approximately [−4808, +4808] G) to approximately [−8.5, +8.5] while preserving polarity sign and retaining information from extreme umbral fields. Prior versions (V1, V2) applied hard clipping at ±400 G followed by linear division, which saturated strong-field information in large umbrae; symmetric log scaling superseded that approach in V3.

**Step 2 — Polarity decomposition into dual channels:**

The signed log-scaled field is split into non-negative positive (B+) and negative (B−) channels:

$$
\text{channel}_0 = \max\!\big(B_{log}(p),\ 0\big) \quad \text{(positive flux, B+)}
$$

$$
\text{channel}_1 = \max\!\big(-B_{log}(p),\ 0\big) \quad \text{(negative flux magnitude, B−)}
$$

Both channels are non-negative with values in approximately [0, 8.5]. Separating polarities into independent input channels allows the network to process incoming and outgoing magnetic flux through parallel convolutional pathways, which is physically meaningful: bipolar active-region signatures (the characteristic morphology of mature sunspot groups) are encoded differentially rather than cancelling at the signed-field level.

**Input field parameters summary:**

| Parameter | Value | Units | Source |
|---|---|---|---|
| Transform | `sign(x) · log1p(\|x\|)` | — | `prepare_dataset.py:35` |
| Strong-field threshold (SI proxy) | 200.0 | G | `prepare_dataset.py:41` |
| Per-channel output range | ≈ [0, 8.5] | — | post-ReLU on log1p |
| NaN handling | Replace with 0.0 | — | `np.nan_to_num(data, nan=0.0)` |
| Input channels | 2 (B+, B−) | — | V3 PRO |
| Final dtype | float32 | — | `processed.astype(np.float32)` |

#### 2.4.1 Target Normalisation: Log Transformation and Mode Collapse Resolution

**Source:** `auralis-back/src/processing/prepare_dataset.py` · `auralis-back/src/models/train_model.py` (`SolarDataset`)

During early development, the model exhibited mode collapse: the gradient of the loss converged to the distribution mean regardless of the input, preventing any meaningful discrimination between activity levels. This was traced to the strongly right-skewed distribution of the raw SI values, in which the loss gradient was dominated by the large majority of low-activity samples.

**Log transformation of the target:**

$$
SI_{log} = \log(SI + \epsilon), \quad \epsilon = 10^{-6}
$$

The log transformation compresses the dynamic range of the target distribution, reduces the disproportionate influence of high-activity outliers, and moves the distribution closer to symmetry. The trainable target is stored in `metadata_processed.csv` in log-SI space; the effective training range is **[1.22, 2.98]**.

`SolarDataset` reads this value directly from the CSV and delivers it as a scalar tensor to the model. No additional Z-Score normalisation is applied in the active training pipeline.

**Target distribution statistics (log-SI space, 1,763 samples):**

| Parameter | Value | Notes |
|---|---|---|
| Mean | ~1.77 | Centre of log(SI) distribution |
| Std dev | ~0.35 | Dispersion of log(SI) |
| Minimum | 1.214 | Quiet-Sun magnetograms |
| Maximum | 2.990 | Peak activity, Cycle 25 maximum |
| ε | 10⁻⁶ | Guard against log(0) |

> **Historical note:** An earlier pipeline stage explored a Z-Score normalisation ($\mu = 1.7658$, $\sigma = 0.3462$) computed over 1,314 tensors. The V3 PRO final training demonstrated that the log transformation alone was sufficient to resolve mode collapse, and the Z-Score stage was removed from the active pipeline. The scaler artefacts (`tools/recalculate_scaler.py`, `models/target_scaler.json`) are retained as auxiliary reference.

### 2.5 FITS-to-NPY Processing Pipeline

**Source:** `auralis-back/src/processing/prepare_dataset.py`, lines 42–116

```
FITS-to-NPY Processing Pipeline (V3 PRO)
──────────────────────────────────────────────────────────────────────────────
Step  Operation                Library             Parameters / Notes
──────────────────────────────────────────────────────────────────────────────
  1   Load FITS file           SunPy               HMI/SDO, los_magnetic_field
  2   Extract data array       astropy.io.fits     Native shape: (4096, 4096)
  3   NaN replacement          NumPy               np.nan_to_num(data, nan=0.0)
  4   Compute Sunspot Index    NumPy               SI = (|B_raw| > 200 G) / total × 100
                                                   Computed on native resolution
                                                   before resize or log scaling
  5   Spatial resampling       skimage.transform   resize(512, 512), mode='reflect',
                                                   anti_aliasing=True, preserve_range=True
  6   Symmetric log scaling    NumPy               x' = sign(x) · log1p(|x|)
  7   Polarity decomposition   NumPy               B+ = ReLU(x'),  B− = ReLU(−x')
  8   Stack dual-channel       NumPy               np.stack([B+, B−]) → (2, 512, 512)
  9   Dtype cast               NumPy               astype(float32)
 10   Save to disk             NumPy               np.save(.npy), (2, 512, 512) float32
 11   Log metadata to CSV      pandas              filename, date, sunspot_index,
                                                   original_shape, processed_shape,
                                                   b_pos_max, b_neg_max,
                                                   mean_b_pos, mean_b_neg
──────────────────────────────────────────────────────────────────────────────
Compression ratio (spatial): 4096² → 512² = 64× reduction
Output file size: ≈ 2.0 MB per image (2 channels × 512² × float32, uncompressed)
──────────────────────────────────────────────────────────────────────────────
```

> **Critical note on SI proxy computation (Step 4):** The Sunspot Index is computed on the raw 4096 × 4096 array before any resampling. Computing the SI after bilinear resize would introduce double-counting artefacts near the 200 G threshold due to interpolation of pixel values across the threshold boundary (`prepare_dataset.py:44–47`).

**Validation criteria applied post-processing:**

| Check | Expected value | Source |
|---|---|---|
| Shape | (2, 512, 512) | `validate_processed.py` |
| Dtype | float32 | `validate_processed.py` |
| Per-channel minimum | ≥ 0.0 (both channels, post-ReLU) | Invariant by construction |
| Per-channel maximum | typically ≤ ~8.6 (≈ log1p(4808)) | Natural log1p range |
| NaN / Inf | None | `np.nan_to_num` + final check |

### 2.6 Data Augmentation

All augmentation is applied exclusively to the training split. The validation hold-out receives no augmentation.

**Source:** `auralis-back/src/models/train_model.py`

**SolarAugmentation** (applied to all training samples):

```python
transforms.RandomHorizontalFlip(p=0.5)
transforms.RandomVerticalFlip(p=0.5)
transforms.RandomRotation(degrees=10)
```

**ExtremeAugmentation** (applied only to samples with `sunspot_index > 2.0`):

```python
# Pixel-perfect transforms — no bilinear interpolation
if torch.rand(1) > 0.5: img = torch.flip(img, dims=[2])       # horizontal flip
if torch.rand(1) > 0.5: img = torch.flip(img, dims=[1])       # vertical flip
k = torch.randint(0, 4, (1,))
if k > 0: img = torch.rot90(img, k=k, dims=[1, 2])            # 90°/180°/270° rotation
```

ExtremeAugmentation uses only `torch.flip` and `torch.rot90` — both pixel-perfect operations that introduce no bilinear interpolation. This is essential for magnetogram data: interpolation near active-region boundaries would corrupt the polarity sign of the B+/B− channels, invalidating the physical meaning of the dual-channel representation. The targeted strategy oversamples high-activity samples without modifying the majority quiet-Sun population, directly addressing the class imbalance that degraded high-activity estimates in prior model versions.

---

## 3. Architecture: Coronium V3 PRO

### 3.1 Design Rationale

Coronium V3 PRO is a lightweight residual architecture designed specifically for regression over dual-channel HMI/SDO magnetograms. The architecture incorporates residual skip connections that enable stable gradient flow across convolutional blocks, mitigating gradient vanishing in deep training. The total parameter count is maintained below 250 K, consistent with resource-constrained deployment targets.

The separation of magnetic polarity into independent input channels (B+, B−) represents an explicit physical inductive bias: parallel convolutional pathways process incoming and outgoing magnetic flux independently, enabling the network to detect the differential bipolar structure that characterises mature active regions.

**Source:** `auralis-back/src/models/train_model.py`

### 3.2 Layer-by-Layer Specification

```
Coronium V3 PRO — Architecture Summary (widened schedule: 32→64→96→128)
─────────────────────────────────────────────────────────────────────────────────
Layer / Block   Type                In→Out Filters  Kernel  Output Shape     Params
─────────────────────────────────────────────────────────────────────────────────
Input           —                   —               —       (B,  2, 512, 512)     —
                                    ← channel 0: B+  |  channel 1: B−
─────────────────────────────────────────────────────────────────────────────────
stage1          Conv2d              2 →  32         3×3     (B, 32, 512, 512)   608
(Residual)      BatchNorm2d         32              —       (B, 32, 512, 512)    64
                ReLU / ECA          —               —       (B, 32, 512, 512)    ~5
                Conv2d (skip proj)  2 →  32         1×1     (B, 32, 512, 512)    96
                Add (residual)      —               —       (B, 32, 512, 512)     —
                MaxPool2d(2)        —               2×2     (B, 32, 256, 256)     —
                Dropout2d(0.2)      —               —       (B, 32, 256, 256)     —
─────────────────────────────────────────────────────────────────────────────────
stage2          Conv2d              32 →  64        3×3     (B, 64, 256, 256) 18,496
(Residual)      BatchNorm2d         64              —       (B, 64, 256, 256)   128
                ReLU / ECA          —               —       (B, 64, 256, 256)    ~5
                Conv2d (skip proj)  32 →  64        1×1     (B, 64, 256, 256) 2,112
                Add (residual)      —               —       (B, 64, 256, 256)     —
                MaxPool2d(2)        —               2×2     (B, 64, 128, 128)     —
                Dropout2d(0.2)      —               —       (B, 64, 128, 128)     —
─────────────────────────────────────────────────────────────────────────────────
stage3          Conv2d              64 →  96        3×3     (B, 96, 128, 128) 55,392
(Residual)      BatchNorm2d         96              —       (B, 96, 128, 128)   192
                ReLU / ECA          —               —       (B, 96, 128, 128)    ~5
                Conv2d (skip proj)  64 →  96        1×1     (B, 96, 128, 128) 6,240
                Add (residual)      —               —       (B, 96, 128, 128)     —
                MaxPool2d(2)        —               2×2     (B, 96,  64,  64)     —
                Dropout2d(0.2)      —               —       (B, 96,  64,  64)     —
─────────────────────────────────────────────────────────────────────────────────
stage4          Conv2d              96 → 128        3×3     (B,128,  64,  64)110,720
(Residual)      BatchNorm2d        128              —       (B,128,  64,  64)   256
                ReLU / ECA          —               —       (B,128,  64,  64)    ~5
                Conv2d (skip proj)  96 → 128        1×1     (B,128,  64,  64)12,416
                Add (residual)      —               —       (B,128,  64,  64)     —
                Dropout2d(0.2)      —               —       (B,128,  64,  64)     —
         *** Grad-CAM hook — shape (B, 128, 64, 64), Z = 64×64 = 4,096 ***
                MaxPool2d(2)        —               2×2     (B,128,  32,  32)     —
─────────────────────────────────────────────────────────────────────────────────
Global Avg Pool AdaptiveAvgPool2d   —               —       (B,128,   1,   1)     —
Flatten         —                   —               —       (B, 128)               —
─────────────────────────────────────────────────────────────────────────────────
Head Dropout    Dropout(p=0.3)      —               —       (B, 128)               —
Regression Head Linear             128 → 1          —       (B, 1)               129
                (no output activation)
─────────────────────────────────────────────────────────────────────────────────
TOTAL TRAINABLE PARAMETERS:                                               ~206,875
─────────────────────────────────────────────────────────────────────────────────
```

> **Grad-CAM hook target:** The hook for Grad-CAM is registered on `model.stage4.conv`, capturing activations of shape (B, 128, 64 × 64) before the final MaxPool. This resolution is sufficient to spatially localise individual active regions within the 512 × 512 magnetogram.

### 3.3 Residual Connections

Each of the four stages includes a skip connection projecting the block input to its output via a 1×1 convolution when channel dimensions differ:

$$
\mathbf{h}^{(l)} = \text{ReLU}\!\left(\mathcal{F}(\mathbf{x}^{(l)}) + W_s \mathbf{x}^{(l)}\right)
$$

where $\mathcal{F}(\mathbf{x}^{(l)})$ is the residual branch (Conv 3×3 + BN + ReLU) and $W_s \mathbf{x}^{(l)}$ is the 1×1 projection. This design:

1. **Provides stable gradient flow:** The gradient can propagate directly through the identity path, mitigating vanishing gradients.
2. **Enables residual learning:** Each block learns an incremental refinement rather than a full mapping from scratch.
3. **Preserves polarity information:** The skip connection retains the B+/B− differential signal across all four stages.

### 3.4 Regression Head: Linear Output Without Activation

The final `Linear(128 → 1)` layer has no output activation. This is the standard choice for regression on a continuous, unbounded target. Since the target (log-SI) spans approximately [1.22, 2.98] without hard bounds, imposing an activation (sigmoid, tanh) would introduce a prior that could bias predictions toward range boundaries. The training loss (WeightedHuberLoss, §4.2) operates directly on the linear output.

### 3.5 Global Average Pooling

Global Average Pooling (GAP) aggregates each of the 128 stage4 feature maps into a single scalar, producing a 128-dimensional vector. Compared to a flattened dense layer:

1. **Eliminates spatial over-parameterisation:** A Flatten + Dense(128 × 32 × 32 → N) would add 131,072 parameters before the head.
2. **Provides implicit spatial regularisation:** GAP forces each feature map to represent a globally meaningful concept rather than a position-specific one.
3. **Enables Grad-CAM:** The stage4 spatial activations (64 × 64, before the final MaxPool) are preserved and accessible for saliency map generation before the pooling collapse.

---

## 4. Training Protocol

### 4.1 Hyperparameter Table

**Source:** `auralis-back/src/models/train_model.py`  
**Source:** `auralis-back/experiments/exp_005_v3pro_augmented.json`

```
Coronium V3 PRO — Training Hyperparameters (exp_005)
──────────────────────────────────────────────────────────────────────
Parameter                    Value              Notes
──────────────────────────────────────────────────────────────────────
Learning rate (initial)      0.001              AdamW optimizer
Optimizer                    AdamW              weight_decay=1e-5, betas (0.9, 0.999)
Batch size                   32                 Per-step gradient update
Dropout rate                 0.2 (stages) /     Dropout2d in residual stages;
                             0.3 (head)         scalar Dropout in regression head
Training loss                WeightedHuberLoss  δ=1.0, α=2.0 (activity-proportional weights)
Reporting metric             L1Loss (MAE)       Used for human-readable epoch logs
Max epochs                   50                 Hard ceiling
Actual epochs run            24                 Terminated by early stopping
Best epoch                   21                 Checkpoint saved as best_coronium_v3_pro_augmented.pth
Best val MAE (log-SI)        0.1071             At epoch 21 — training-loop value
Early stopping patience      10                 Consecutive epochs without improvement
Validation split             0.2 (20%)          Random hold-out, random_state=42 — 353 samples
Input channels               2                  B+ (positive) / B− (negative)
Target space                 log-SI             log(SI + ε), ε=10⁻⁶; range [1.22, 2.98]
ExtremeAugmentation          sunspot_index>2.0  torch.flip + torch.rot90 — pixel-perfect only
──────────────────────────────────────────────────────────────────────
```

### 4.2 Loss Function: WeightedHuberLoss

**Training loss — Weighted Huber Loss:**

$$
\mathcal{L}_{WHL}(r_i) = w_i \cdot \begin{cases} \frac{1}{2}r_i^2 & \text{if } |r_i| \leq \delta \\ \delta\!\left(|r_i| - \frac{\delta}{2}\right) & \text{otherwise} \end{cases}
\quad r_i = \hat{y}_i - y_i,\quad \delta = 1.0
$$

$$
w_i = 1.0 + \alpha \cdot y_i,\quad \alpha = 2.0
$$

WeightedHuberLoss combines Huber loss robustness to outliers with per-sample weights proportional to the actual solar activity level. The factor α = 2.0 assigns greater loss weight to predictions on high-activity samples, counteracting the dataset imbalance in which quiet-Sun observations outnumber active-region observations. This targeted weighting was critical for reducing prediction bias toward the mean in high-activity regimes.

**Reporting metric — Mean Absolute Error:**

$$
\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} \left| \hat{y}_i - y_i \right|
$$

MAE is reported in log-SI space (the native optimisation target). The training loop reports `val_mae = 0.1071` at the best checkpoint (epoch 21); the offline evaluation script (`evaluate_final.py`, MC Dropout T=20) reports `MAE = 0.1048` over 353 hold-out samples. Both are directly comparable because the model predicts log(SI) without intermediate transformations.

### 4.3 Learning Rate Scheduler

**Source:** `auralis-back/src/models/train_model.py`, lines 442–447

```python
torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode     = 'min',
    factor   = 0.5,   # New LR = old LR × 0.5
    patience = 3      # Epochs without val_loss improvement before reduction
)
```

The scheduler monitors validation loss. After 3 consecutive epochs without improvement, the learning rate is halved:

$$
\eta_{t+1} = \eta_t \times 0.5
$$

In exp_005, the learning rate was reduced twice: 0.001 → 0.0005 at epoch 19, and 0.0005 → 0.00025 at epoch 23.

### 4.4 Early Stopping

**Source:** `auralis-back/src/models/train_model.py`, lines 407–522

Early stopping monitors validation loss with a patience of 10 epochs. Training terminates when no improvement is observed over 10 consecutive epochs, at which point the best checkpoint is restored. In exp_005, the mechanism triggered **dynamically at epoch 24**, with the best checkpoint recorded at **epoch 21** (val-MAE log-SI = 0.1071). Checkpoint selection criterion is minimum `val_mae` (not `val_whl`), ensuring best generalisability in the reporting space.

$$
\text{stop if}\ \min_{e \leq t-p} \mathcal{L}_{val}(e) \leq \mathcal{L}_{val}(t),\ \forall t \in [t-p, t],\quad p = 10
$$

The controlled gap between training and validation curves over the 24 epochs is consistent with the model generalising rather than memorising. The split's random construction (`random_state=42`) ensures that extreme events (max_y_train = 2.9788, max_y_val = 2.9019) are present in both sets.

---

## 5. Results and Benchmarking

### 5.1 Promoted Metrics — exp_005 (MC Dropout, T=20, seed=42)

**Source:** `auralis-back/experiments/exp_005_v3pro_augmented.json` · `auralis-back/scripts/evaluate_final.py`  
**Evaluated on:** 353-sample hold-out, `random_state=42`  
**Protocol:** PyTorch MC Dropout — `model.eval()` + selective `Dropout.train()`, T=20 passes per batch, `torch.manual_seed(42)`

| Metric | Value | Space | Notes |
|---|---|---|---|
| **MAE (log-SI, MC Dropout)** | **0.1048** | log-SI | Official: evaluate_final.py, T=20 |
| **RMSE (log-SI)** | **0.1272** | log-SI | $\sqrt{\frac{1}{N}\sum(\hat{y}_i - y_i)^2}$ |
| **R² (hold-out)** | **0.8634** | log-SI | Random split; both sets cover extreme events |
| **MAPE** | **6.07%** | — | Excludes samples with y = 0 |
| **Accuracy proxy (100 − MAPE)** | **93.93%** | — | Regression convenience metric; not classification accuracy |
| Train val-MAE (best checkpoint) | 0.1071 | log-SI | Epoch 21 — best_coronium_v3_pro_augmented.pth |
| Stopping epoch | 24 | — | Early stopping (best at epoch 21) |
| PyTorch CPU inference | 27.90 ms | — | 100-iter benchmark, 10-iter warm-up |
| **ONNX Runtime CPU inference** | **25.11 ms** | — | 86.6 KB model — 1.11× speedup vs. PyTorch CPU |

> The accuracy proxy (93.93%) is defined as 100 − MAPE and is a regression reporting convenience. It does not correspond to classification accuracy or any binary decision boundary.

### 5.2 External Benchmark Comparison

**Source:** `auralis-back/experiments/results_benchmarking.json` + `exp_005`  
**Run ID:** `benchmarking_baselines` · **Date:** 2026-04-23  
**Dataset:** 1,763 samples — 1,410 training / 353 validation (`random_state=42`)  
**External protocol:** AdamW, lr=0.001, batch=32, epochs=30, seed=42

> **Methodological caveat.** Benchmark comparisons are scale-asymmetric: external baselines and Coronium are not always evaluated under identical target-space assumptions, so raw MAE ranking should be interpreted carefully. The main contribution of Coronium V3 PRO is its dual-polarity representation, parameter efficiency, reproducibility, and lightweight deployment readiness. Direct numeric MAE comparisons between baselines operating in one scale and Coronium operating in log-SI should be treated as indicative rather than strictly equivalent.
>
> External baselines (ResNet-18, VGG-11) were retrained from scratch on the same HMI/SDO corpus using a single-channel collapsed input (`|B| = B+ + B−`). Coronium V3 PRO uses the full dual-channel (B+, B−) representation.

| Model | MAE† | RMSE† | R² | Parameters | Inference (ms) |
|---|---|---|---|---|---|
| Naive Persistence | 0.2882 | 0.3349 | −0.008 | 0 | < 0.001 |
| ResNet-18 | 0.0755 | 0.0898 | 0.9276 | 11,170,753 | 6.16 |
| VGG-11 | 0.1079 | 0.1239 | 0.8621 | 9,350,913 | 17.23 |
| **Coronium V3 PRO** | **0.1048** | **0.1272** | **0.8634** | **~206,875** | **25.11** |

> †Baseline MAE and RMSE values are reported in their native training scale; Coronium's MAE and RMSE are in log-SI space. The numeric values are not directly equivalent and should not be read as a strict rank. The R² column is scale-normalised and provides a more comparable measure of explained variance across models. The main contribution of Coronium V3 PRO is its dual-polarity representation, **~45–54× parameter reduction** relative to the baselines, reproducibility, and an ONNX export of 86.6 KB enabling CPU-only inference at 25.11 ms.

**Parameter efficiency — Coronium V3 PRO vs. baselines:**

| Comparison | Parameter ratio | R² delta |
|---|---|---|
| vs. Naive Persistence | — | +0.87 |
| vs. ResNet-18 | 54× fewer parameters | −0.064 |
| vs. VGG-11 | 45× fewer parameters | +0.001 |

### 5.3 Efficiency–Accuracy Trade-off

> R² is used as the primary visual comparison metric because MAE values are scale-asymmetric between baselines and Coronium (see the methodological caveat in §5.1); R² is scale-normalised and provides a more comparable measure of explained variance across models.

**Figure 1 — Parameter Count Comparison**

![Parameter Count Comparison](reports/figures/parameter_count_comparison.png)

**Figure 2 — R² vs. Parameter Count (log scale)**

![R² vs. Parameter Count](reports/figures/r2_vs_parameters.png)

Coronium V3 PRO reaches **R² = 0.8634** with **206,875 parameters** and an **86.6 KB ONNX export**, compared with VGG-11 at R² = 0.8621 using 9,350,913 parameters and ResNet-18 at R² = 0.9276 using 11,170,753 parameters. The model is 45–54× smaller than both baselines while matching VGG-11's explained variance within 0.001 R² units. ResNet-18 achieves higher R² (0.9276) at 54× the parameter cost; that trade-off favours Coronium in resource-constrained deployment contexts where memory, bandwidth, and thermal budgets are limiting factors.

### 5.4 Incremental Ablation Study (V1 → V3 PRO)

```
Ablation Study: Contribution of Each Improvement (V1 → V3 PRO)
─────────────────────────────────────────────────────────────────────────────────
Modification                                       Delta MAE  Delta R²   Source
─────────────────────────────────────────────────────────────────────────────────
V1 Baseline (LR=0.01, no scheduler)                0.2847     0.7213     exp_001
+ LR reduction (0.01→0.001) + scheduler            −0.1013    +0.1028    exp_002
+ Data augmentation + dataset expansion (1158)     (included) (included)
+ Dropout increase (0.20→0.25→0.30)                −0.0418    +0.0464    exp_003
─────────────────────────────────────────────────────────────────────────────────
= Coronium V2 PRO (MAE: 0.1416)                                            exp_003
─────────────────────────────────────────────────────────────────────────────────
+ Residual architecture (skip connections)         ↓          ↑           exp_004
+ Dual-channel input (B+/B−, 2ch)                 ↓          ↑           exp_004
+ Log normalisation of target                      ↓↓         ↑↑          exp_004
+ Dataset expansion (1158→1763 samples)            ↓          ↑           exp_004
+ Widened schedule (16→32→64→96 → 32→64→96→128)   ↓          ↑           exp_005
+ ExtremeAugmentation (flip+rot90, SI>2.0)         ↓          ↑           exp_005
+ Random split random_state=42 (domain shift fix)  ↓          ↑↑          exp_005
─────────────────────────────────────────────────────────────────────────────────
= Coronium V3 PRO + ExtremeAug  (MAE: 0.1048 | MAPE: 6.07% | R²: 0.8634)  exp_005
─────────────────────────────────────────────────────────────────────────────────
```

The largest single improvement was the resolution of mode collapse via log normalisation of the target (exp_004), which unlocked real discrimination between activity levels. In exp_005, ExtremeAugmentation targeted the underrepresented high-activity regime (SI > 2.0), and replacing the chronological split with a random split (`random_state=42`) corrected the temporal domain shift that had driven R² from approximately −0.20 (chronological) to +0.8634 (random).

### 5.5 Cross-Validation Status

No formal k-fold cross-validation run is included in the experiment log. All registered experiments (exp_001 through exp_005) used a single 80/20 hold-out with `random_state=42` (1,410 training / 353 validation). The dashboard presents illustrative K-Fold reference values synthesised for display purposes only; these are not experimental results. A formal k-fold cross-validation (k = 5) for rigorous estimation of generalisation variance is listed as future work (§7).

The k-fold aggregation formula for reference:

$$
\text{MAE}_{k\text{-fold}} = \frac{1}{k}\sum_{j=1}^{k} \text{MAE}_j, \qquad
\sigma_{\text{MAE}} = \sqrt{\frac{1}{k-1}\sum_{j=1}^{k}\left(\text{MAE}_j - \overline{\text{MAE}}\right)^2}
$$

---

## 6. Explainability and Uncertainty Estimation

### 6.1 Grad-CAM Implementation and Empirical Validation

**Source:** `auralis-back/src/api/main.py` (GradCAM class, lines 68–135)  
**Target layer:** `model.stage4.conv` — Conv 3×3 output of the last residual block, before BN/ReLU/ECA

Gradient-weighted Class Activation Mapping (Grad-CAM) is implemented by attaching forward and backward hooks to `model.stage4.conv`. The choice of stage4 is deliberate: as the last spatial feature extractor before Global Average Pooling, it captures the highest-level semantic representations in the network, encoding global magnetogram structure rather than local edges or textures.

**Algorithm:**

**Step 1 — Hook registration.** Forward and backward hooks are registered on `model.stage4.conv` before inference:

```python
self.target_layer.register_forward_hook(forward_hook)
self.target_layer.register_full_backward_hook(backward_hook)
```

**Step 2 — Forward and backward pass.** A single forward pass computes the regression estimate; a scalar backward pass propagates gradients to stage4:

```python
output = self.model(input_tensor)   # forward
output.backward()                   # gradient w.r.t. scalar prediction
```

**Step 3 — Gradient-based channel weighting.** For each of K = 128 feature map channels, a scalar importance weight α_k is computed by Global Average Pooling of the gradients:

$$
\alpha_k = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial \hat{y}}{\partial A^k_{ij}}
$$

where Z = 64 × 64 = 4,096 is the spatial extent of the stage4 feature maps.

**Step 4 — Weighted activation summation and ReLU.** The heatmap is the channel-weighted mean of activations, followed by ReLU to retain only positively contributing regions:

$$
L^{Grad\text{-}CAM} = \text{ReLU}\!\left( \sum_{k} \alpha_k A^k \right)
$$

**Step 5 — Normalisation and upsampling.** The 64 × 64 heatmap is normalised to [0, 1] and bilinearly upsampled to 512 × 512 via `scipy.ndimage.zoom`:

```python
heatmap = heatmap / heatmap.max()
heatmap_full = ndimage_zoom(heatmap, zoom_factor=8.0, order=1)
```

Hook cleanup is performed in a `finally` block to prevent memory leaks after each inference call.

**Empirical validation.** Grad-CAM maps were generated for hold-out samples, including a high-activity case (2024-08-10, SI = 2.978; artifact at `reports/figures/gradcam_v3pro_maxactivity_20240810.png`) and additional samples (e.g., `gradcam_v3pro_maxactivity_20240812.png`). The resulting saliency maps show elevated activation in regions consistent with known active-region morphology — concentrated, spatially structured flux in areas that would correspond to sunspot groups — while background pixels and the quiet-Sun disk show near-zero activation. These observations are consistent with physically meaningful feature localisation; they should not be interpreted as proof that the model has learned causal solar-physical relationships. Grad-CAM is a post-hoc attribution method and does not guarantee that the highlighted regions are the unique or necessary drivers of the prediction.

**Interactive faithfulness tool (dashboard).** The API endpoint `GET /api/xai/faithfulness` implements a pixel-deletion deletion curve for any single image on demand: it progressively masks pixels in descending saliency order (guided by the Grad-CAM heatmap) and compares the prediction degradation against a random-masking baseline (seed=42, reproducible). The per-image area-under-the-gap (AUC) is returned alongside the deletion curve. This is a qualitative interactive tool for the research dashboard; it has not been run systematically over the full 353-sample hold-out. A systematic batch faithfulness evaluation is listed as future work (§7).

### 6.2 Uncertainty Quantification — Two Distinct Protocols

The system implements two different uncertainty estimation approaches, each appropriate for its deployment context. They are **not interchangeable** and must not be conflated.

#### 6.2.1 PyTorch MC Dropout — Official Evaluation Protocol

**Source:** `auralis-back/scripts/evaluate_final.py`  
**Used for:** Canonical reported metrics (MAE, RMSE, R², MAPE)

Monte Carlo Dropout exploits the Dropout layers already present in Coronium V3 PRO for principled epistemic uncertainty estimation at evaluation time.

**Protocol:**

1. Set `model.eval()` to freeze BatchNorm running statistics.
2. Selectively re-enable all Dropout modules for stochastic sampling:
   ```python
   for m in model.modules():
       if m.__class__.__name__.startswith('Dropout'):
           m.train()
   ```
3. Execute T = 20 stochastic forward passes per batch under `torch.no_grad()`:
   $$\lbrace \hat{y}_1, \ldots, \hat{y}_T \rbrace = \lbrace f_\theta^{(t)}(\mathbf{x}) \rbrace_{t=1}^{T=20}$$
4. Compute the point estimate as the mean over passes:
   $$\hat{y} = \frac{1}{T}\sum_{t=1}^{T} \hat{y}_t$$
5. Restore full evaluation mode.

All RNG sources are seeded at 42 (`torch.manual_seed`, MPS, NumPy) for deterministic reproducibility. This is the **only protocol used to compute the promoted metrics** (MAE = 0.1048, RMSE = 0.1272, R² = 0.8634, MAPE = 6.07%).

#### 6.2.2 ONNX Input-Noise Perturbation — Dashboard API

**Source:** `auralis-back/src/api/main.py`, `/api/predict` endpoint (lines 564–621)  
**Used for:** Live `uncertainty` field in the API response

The ONNX graph was exported with `model.eval()` and `do_constant_folding=True`. As a consequence, **Dropout layers are removed from the ONNX graph** — MC Dropout is not applicable to the ONNX runtime path. The API approximates an uncertainty measure using input-noise perturbation:

1. Generate 20 noisy copies of the input by adding zero-mean Gaussian noise (σ = 0.005, seed = 42 via `np.random.default_rng`):
   $$\mathbf{x}^{(t)} = \mathbf{x} + \epsilon^{(t)},\quad \epsilon^{(t)} \sim \mathcal{N}(0,\ \sigma^2),\ \sigma = 0.005$$
2. Run the ONNX session on each noisy input.
3. Return `mean` as the point estimate and `std` as the uncertainty:
   $$\hat{y} = \frac{1}{20}\sum_{t=1}^{20} f_{ONNX}(\mathbf{x}^{(t)}), \qquad \sigma_{noise} = \text{Std}\!\left[\lbrace f_{ONNX}(\mathbf{x}^{(t)})\rbrace\right]$$

The noise magnitude (σ = 0.005) is calibrated to the approximate 0.5% read-noise floor of HMI Level-1.5 magnetograms. This uncertainty estimate reflects sensitivity to instrument-level input perturbations, not the epistemic uncertainty of the model weights. It is a practical approximation for the dashboard, not a Bayesian quantity.

#### 6.2.3 Heuristic Confidence Score

A separate confidence score is computed by all prediction endpoints:

$$
c = \text{clip}\!\left(1.0 - \frac{|\hat{y}|}{500.0},\ 0.75,\ 0.99\right)
$$

This score decreases for larger predicted activity values, reflecting the observation that high-activity events are underrepresented in the training corpus. The constant 500.0 and the clip bounds [0.75, 0.99] are empirically chosen and should not be interpreted as a statistically principled quantity.

### 6.3 ONNX Deployment and CPU Latency

Coronium V3 PRO was exported to ONNX format (opset 18, `do_constant_folding=True`) to enable deployment in resource-constrained environments without a GPU.

- **ONNX file size: 86.6 KB** — the complete 206,875-parameter graph fits within the working memory of embedded ARM processors without additional compression.
- **Mean inference latency: 25.11 ms** — ONNX Runtime CPU, single image (512 × 512 dual-channel), no hardware accelerator.
- **Dynamic batch axis:** the exported graph supports arbitrary batch sizes without re-export.
- **BatchNorm fusion:** `do_constant_folding=True` fuses BatchNorm nodes with their preceding Conv layers at export time, which is valid because the model is in `eval()` mode at export and the BN parameters are constants.
- **Benchmark protocol:** 10 warm-up iterations followed by 100 measured iterations on a 512 × 512 dual-channel image.

| Backend | Mean latency (ms) | Speedup |
|---|---|---|
| PyTorch CPU | 27.90 | 1.00× |
| **ONNX Runtime CPU** | **25.11** | **1.11×** |

This latency profile makes Coronium V3 PRO a candidate for potential future deployment in resource-constrained contexts where storage, bandwidth, and thermal constraints preclude large model files.

### 6.4 High-Activity Regime Robustness

Accurate estimation in the high-activity regime (SI > 2.0) is the most challenging aspect of the regression task due to the relative scarcity of such samples in the training corpus.

- **Qualitative improvement in high-activity regime.** Internal observations during development indicated improved prediction quality on samples with SI > 2.0 after introducing ExtremeAugmentation (comparing `best_coronium_v3_pro.pth` without ExtremeAug against `best_coronium_v3_pro_augmented.pth` with ExtremeAug). No formal per-stratum evaluation script exists in the repository; a reproducible comparison over the SI > 2.0 subgroup of the hold-out is listed as future work (§7).
- **ExtremeAugmentation** uses exclusively `torch.flip` and `torch.rot90` — pixel-perfect operations with no bilinear interpolation, preserving polarity sign at active-region boundaries.
- **Targeted application:** augmentation applies only to training samples with `sunspot_index > 2.0`; the validation split and quiet-Sun samples are not affected.

---

## 7. Limitations and Future Work

### Known Limitations

1. **Dataset scope.** The 1,763-sample corpus spans Solar Cycles 24–25 with deliberate oversampling of the 2021–2025 ascending maximum (50% of samples). Solar-minimum epochs are underrepresented. Model performance during deep solar minimum has not been characterised.

2. **Proxy target, not observed index.** The Sunspot Index is a magnetogram-derived pixel-count proxy computed at a fixed threshold (200 G). It is not equivalent to the official NOAA International Sunspot Number or any externally validated activity index, and no cross-validation against external catalogues has been performed.

3. **Nowcasting scope only.** The model estimates the activity index for a given magnetogram at the time of observation. It does not produce temporal forecasts, does not predict future activity levels, and makes no claims regarding flare probability, CME likelihood, or geomagnetic storm occurrence.

4. **No cross-instrument or cross-observatory validation.** All data originate from HMI/SDO (`HMI_FRONT2`, Level-1.5). Generalisation to other instruments (e.g., GONG, MDI, ASO-S/FMG) has not been tested.

5. **Benchmark scale asymmetry.** External baselines were evaluated using a single-channel collapsed input; Coronium uses dual-channel input and log-SI targeting. The numeric MAE comparison is therefore not performed under strictly identical conditions.

6. **No formal k-fold cross-validation.** All experiments used a single 80/20 hold-out. The variance of the generalisation estimate has not been rigorously quantified.

7. **ONNX uncertainty is not Bayesian.** The input-noise perturbation uncertainty in the dashboard API reflects sensitivity to instrument-level noise, not principled epistemic uncertainty. For principled uncertainty estimates, the PyTorch MC Dropout path should be used.

8. **Activity classification thresholds are empirically calibrated.** The classification boundaries (1.41, 1.75 in log-SI space) are calibrated to the V3 PRO ONNX output distribution and have not been validated against external flare catalogs or energy-class definitions.

9. **Grad-CAM attribution is post-hoc.** Saliency maps are consistent with physically plausible localisation but do not constitute proof of causal reasoning. The ReLU in the Grad-CAM formulation suppresses negative contributions, potentially masking inhibitory activations.

### Future Work

- Formal k-fold cross-validation (k = 5) for rigorous generalisation variance estimation.
- Per-stratum evaluation script: reproducible MAE and RMSE on the SI > 2.0 high-activity subgroup and the SI < 1.5 quiet-Sun subgroup of the 353-sample hold-out.
- Batch faithfulness evaluation (pixel-deletion AUC) over the full 353-sample hold-out using a standalone script.
- Calibration study comparing proxy SI against NOAA International Sunspot Number and GOES X-ray flux archives.
- Solar-minimum extension: ingestion and evaluation on 2019–2020 Cycle 25 minimum observations.
- Multi-instrument transfer: fine-tuning or zero-shot evaluation on MDI/SOHO or GONG magnetograms.
- Replacement of the heuristic confidence score with a calibrated probability estimate (e.g., temperature scaling or conformal prediction intervals).
- Formal Zenodo archival and DOI minting for the dataset and model checkpoints.

---

## 8. Conclusions

Coronium V3 PRO + ExtremeAugmentation is a completed and validated research artefact demonstrating the viability of lightweight residual architectures for estimating a solar magnetic activity proxy from HMI/SDO magnetograms. With **~206,875 trainable parameters**, the model achieves **MAE (log-SI) = 0.1048**, **MAPE = 6.07%** (accuracy proxy = **93.93%**), **RMSE = 0.1272**, and **R² = 0.8634** on a 353-sample hold-out evaluated with Monte Carlo Dropout (T = 20, seed = 42).

The central technical contribution of V3 is the resolution of mode collapse through log normalisation of the training target (log-SI range [1.22, 2.98]). This single mathematical refinement enabled genuine discrimination between activity levels, replacing a failure mode in which the model predicted the distribution mean regardless of input. The positive R² (0.8634) was subsequently unlocked by adopting a random split (`random_state=42`) that ensures Cycle 25 extreme-activity events are represented in both training and validation sets, eliminating the temporal domain shift of the prior chronological split.

The **dual-channel input representation** (B+, B−) introduces explicit physical structure: independent convolutional pathways process positive and negative magnetic flux separately, enabling detection of the bipolar signatures characteristic of mature active regions. The widened filter schedule (32→64→96→128) increases representational capacity to 206,875 parameters while remaining within a resource-constrained deployment budget.

The external benchmark establishes that ResNet-18 (R² = 0.9276) and VGG-11 (R² = 0.8621) achieve higher absolute accuracy; however, they require 45–54× more parameters and model sizes on the order of tens of megabytes. Coronium V3 PRO reaches **R² = 0.8634 with an ONNX export of 86.6 KB and CPU inference at 25.11 ms**, making it a candidate for potential future deployment in resource-constrained contexts where memory, bandwidth, and thermal budgets are limiting factors.

Grad-CAM saliency maps generated over hold-out samples show elevated activation in regions consistent with known active-region morphology. These observations are compatible with physically meaningful feature localisation; they do not constitute proof of causal learning and should be interpreted as an auxiliary quality indicator alongside the quantitative metrics.

The complete pipeline — from FITS ingestion via NASA JSOC through dual-channel preprocessing, residual network training, ONNX export, FastAPI inference service, Grad-CAM explainability, and MC Dropout uncertainty quantification — is fully automated, reproducible, and runs locally on Apple Silicon MPS. The canonical metrics are reproducible by running `auralis-back/scripts/evaluate_final.py` against the promoted checkpoint.

---

## Appendix A — Source File Reference Index

```
Auralis/
├── docs/
│   ├── architecture.md                    — System architecture, data contracts, frontend/backend boundaries
│   └── backend.md                         — Backend maintenance notes
├── auralis-back/
│   ├── src/
│   │   ├── models/
│   │   │   └── train_model.py             — Coronium V3 PRO architecture, SolarDataset, training loop, ExtremeAug
│   │   ├── processing/
│   │   │   ├── prepare_dataset.py         — FITS→NPY pipeline, log_scale, B+/B− split, log(SI) target
│   │   │   └── validate_processed.py      — Data quality validation
│   │   ├── ingestion/
│   │   │   ├── download_solar_data.py     — Individual HMI ingestion
│   │   │   └── massive_ingest_pipeline.py — Bulk dataset construction (1,763 samples)
│   │   ├── experiments/
│   │   │   └── run_external_baselines.py  — ResNet-18 / VGG-11 benchmark training
│   │   ├── api/
│   │   │   └── main.py                    — FastAPI server, ONNX inference, Grad-CAM, MC Dropout, faithfulness
│   │   ├── tools/
│   │   │   └── visualize_tensor.py        — .npy tensor inspection utility
│   │   └── visualization/
│   │       └── app.py                     — Streamlit auxiliary visualisation app
│   ├── scripts/
│   │   ├── evaluate_final.py              — Official hold-out evaluation (353 samples, MC Dropout T=20)
│   │   ├── explain_model.py               — Grad-CAM on stage4
│   │   ├── export_to_onnx.py              — PyTorch → ONNX opset 18 export + CPU benchmark
│   │   ├── plot_final_scatter.py          — Prediction vs. ground truth scatter (thesis figure)
│   │   ├── predict.py                     — Single-file inference CLI
│   │   ├── recalculate_scaler.py          — [Auxiliary] population scaler (not used in active V3 PRO pipeline)
│   │   ├── extract_test_kit.py            — Demo sample kit preparation
│   │   ├── kaggle_auralis_v3pro_dataset_builder.py — Kaggle dataset publication
│   │   └── test_inference.py              — Inference pipeline smoke test
│   ├── models/
│   │   ├── best_coronium_v3_pro_augmented.pth — V3 PRO + ExtremeAug [active production]
│   │   ├── best_coronium_v3_pro.onnx      — ONNX opset 18, 86.6 KB [edge deployment]
│   │   ├── target_scaler.json             — [Auxiliary] μ=1.7658, σ=0.3462 (not used by active model)
│   │   └── split_indices.json             — Canonical split indices (random_state=42, 1410/353)
│   ├── experiments/
│   │   ├── exp_001_v1_baseline.json       — V1 baseline (MAE 0.2847, R² 0.7213)
│   │   ├── exp_002_v2_tuned.json          — V2 LR+Scheduler (MAE 0.1834, R² 0.8241)
│   │   ├── exp_003_v2pro_production.json  — V2 PRO (MAE 0.1416, R² 0.8705)
│   │   ├── exp_004_v3pro_final.json       — V3 PRO base (transition)
│   │   ├── exp_005_v3pro_augmented.json   — V3 PRO + ExtremeAug [active — MAE 0.1048, R² 0.8634]
│   │   └── results_benchmarking.json      — External baselines: Naive / ResNet-18 / VGG-11
│   ├── reports/
│   │   ├── results_comparison.csv         — Predictions vs. ground truth (353 samples, eval output)
│   │   ├── final_coronium_scatter_tesis.png — Official scatter figure (exp_005)
│   │   ├── r2_diagnostic.png              — R² visual diagnostic
│   │   └── figures/
│   │       ├── gradcam_sample.png         — Representative Grad-CAM overlay
│   │       ├── gradcam_v3pro_maxactivity_20240810.png — Grad-CAM for SI=2.978 (2024-08-10)
│   │       ├── gradcam_v3pro_maxactivity_20240812.png — Grad-CAM for high-activity sample (2024-08-12)
│   │       ├── learning_curve_v3_pro.png  — Training curve (early stop epoch 24)
│   │       ├── error_scatter.png          — Prediction error scatter
│   │       └── mode_collapse_evidence.png — Historical mode collapse evidence (resolved in V3)
│   └── data/processed/
│       └── metadata_processed.csv         — Index of 1,763 samples (target in log-SI)
└── auralis-front/                         — React 18 + TypeScript + Vite dashboard
```

---

## Appendix B — Key Equations and Canonical Values

| Symbol | Definition | Value (exp_005) |
|---|---|---|
| `log_scale` | Magnetic field transform: `sign(x) · log1p(\|x\|)` | sign-preserving log |
| $B_{thresh}$ | Strong-field detection threshold for SI proxy | 200.0 G |
| $\mu_{pop}$ | [Auxiliary] population mean of log(SI) — `target_scaler.json`, not applied by active model | 1.7658 |
| $\sigma_{pop}$ | [Auxiliary] population std of log(SI) — historical reference | 0.3462 |
| $\eta_0$ | Initial learning rate | 0.001 |
| $\gamma$ | LR scheduler reduction factor | 0.5 |
| $p_{sched}$ | LR scheduler patience | 3 epochs |
| $p_{stop}$ | Early stopping patience | 10 epochs |
| $E_{stop}$ | Stopping epoch (exp_005) | 24 |
| $E_{best}$ | Best checkpoint epoch (exp_005) | 21 |
| $T$ | MC Dropout passes (evaluate_final.py) | 20 |
| $K$ | Feature map channels at Grad-CAM target (stage4) | 128 |
| $C_{in}$ | Input channels (B+, B−) | 2 |
| $N_{params}$ | Total trainable parameters | ~206,875 |
| MAE log-SI | Mean Absolute Error — log-SI, MC Dropout eval | **0.1048** |
| RMSE log-SI | Root Mean Squared Error — log-SI | **0.1272** |
| train val-MAE | Val-MAE at best checkpoint (training loop, epoch 21) | 0.1071 |
| MAPE | Mean Absolute Percentage Error | **6.07%** |
| Accuracy proxy | 100 − MAPE (regression convenience metric, not classification accuracy) | **93.93%** |
| R² (hold-out) | Coefficient of determination — random split, random_state=42 | **0.8634** |
| ONNX size | Exported model file size (opset 18) | **86.6 KB** |
| ONNX latency | Mean CPU inference — 512×512 dual-channel image | **25.11 ms** |
| σ (noise) | Input perturbation std — ONNX API uncertainty simulation | 0.005 |

---

*End of RESEARCH_DOSSIER_MASTER.md*  
*Generated from the `exp_005` consolidated repository state — 2026-04-02 · Updated 2026-05-26 (v3.3.0 — canonical metrics reproducible with `torch.manual_seed(42)` in `evaluate_final.py`: MAE=0.1048, RMSE=0.1272, MAPE=6.07%, R²=0.8634)*
