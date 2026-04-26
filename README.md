# Coronium V3 PRO — Auralis

**High-efficiency regression framework for solar activity prediction from HMI/SDO magnetograms.**

Full-stack system validated for near-real-time estimation of the sunspot index: JSOC ingestion → HMI preprocessing → CNN inference → REST API + interactive dashboard.

---

## Performance

| Metric | Value | Condition |
|:---|:---:|:---|
| Physical MAE (real scale) | **0.3167** | Raw targets vs. denormalized predictions — official output metric |
| Z-Score MAE | 0.1380 | Error in optimization space (internal training comparison) |
| MAPE | **5.52%** | Accuracy above 94% |
| R² (analytical) | **~0.81** | Computed in Z-Score space during training |
| Inference Latency | **8.7 ms** | Single sample, Apple M-series MPS |

---

## Architecture

Coronium V3 PRO is a lightweight residual architecture with under 500K parameters, optimized for Apple Silicon (MPS). It accepts **dual-channel** input (2, 512, 512) that physically separates positive (B+) and negative (B−) magnetic polarity from the magnetogram. Global Average Pooling collapses each activation map to a scalar before the regression head, eliminating the O(H·W·C) cost of a dense layer. The result is a model that achieves over 94% accuracy with under 500K parameters versus 9.35M for VGG-11.

```
Input (2, 512, 512)  ← channel 0: B+  |  channel 1: B−
  └─ Residual Block ×4  [16→32→64→96 ch, ECA Attention, BatchNorm, Dropout2d, MaxPool2d]
       └─ Global Average Pooling  →  (96,)
            └─ Linear(96, 1)  →  sunspot index
```

> Baselines evaluated with |B| = B+ + B− input (1 channel, raw physical scale) — fair 1-channel vs. 2-channel comparison.  
> Coronium V3 PRO physical MAE: **0.3167**. Z-Score MAE (training loop): 0.1380.

| Model | Parameters | Physical MAE | R² | Latency |
|:---|---:|:---:|:---:|:---:|
| **Coronium V3 PRO** | **~88 K** | **0.3167** | **~0.81** | **8.7 ms** |
| ResNet-18 | 11.2 M | 0.0755 | 0.9276 | 6.16 ms |
| VGG-11 | 9.35 M | 0.1079 | 0.8621 | 17.23 ms |
| Naive Persistence | 0 | 0.2882 | −0.008 | < 1 ms |

---

## Mode Collapse Fix — The Mathematical Solution

The mode collapse problem (model collapsing toward a constant prediction) was diagnosed and eliminated through a two-phase normalization applied over the real target distribution:

1. **Logarithmic normalization** — compresses the distribution of extreme solar index values.
2. **Population Z-Score** — standardizes using statistics computed over **1,314 real tensors**:

$$\mu_{pop} = 1.7658 \qquad \sigma_{pop} = 0.3462$$

$$z = \frac{\log(SI) - \mu_{pop}}{\sigma_{pop}}$$

This transformation guaranteed that the loss gradient never collapsed to zero and that the model learned to discriminate between magnetic activity levels.

---

## Dataset

| Metric | Value |
|:---|:---:|
| Total curated samples | **1,763** |
| Training (with data augmentation) | **1,411** |
| Validation (isolated hold-out) | **352** |
| Format | NumPy binary (.npy), float32 |
| Processed resolution | 512 × 512 px |

---

## Scientific Features

**Explainability — Grad-CAM (XAI)**
Grad-CAM was implemented by hooking the `stage4` layer. The generated heatmaps empirically demonstrated that the AI focuses its attention surgically **exclusively on active magnetic regions** (sunspots), completely ignoring the space background and instrumental noise. This validates that the model learned real physics, not statistical artifacts.

**Uncertainty Quantification — Monte Carlo Dropout**
At inference time, Dropout2d layers are reactivated and N stochastic forward passes are executed to produce a predictive mean and variance. This provides a calibrated uncertainty estimate without retraining.

---

## Training System

- **Dynamic Early Stopping:** halted training at **Epoch 43**, automatically detecting the peak generalization point.
- **No memorization:** the gap between training and validation loss remained controlled throughout the cycle, confirming the model does not overfit.
- **Device:** Apple Silicon MPS, PyTorch 2.2.0.

---

## System Architecture

```
NASA JSOC (HMI Level-1.5)
  └─ ingestion/            SunPy/Fido download, exponential-backoff retry
       └─ processing/      FITS → float32 .npy, B+/B− polarity, log + Z-score norm
            └─ models/     Coronium V3 PRO — training + inference engine
                 └─ api/   FastAPI REST  (predict, gradient-cam, benchmarks)
                      └─ auralis-front/   React 18 + TypeScript dashboard
```

---

## Tech Stack

**Backend**
| Layer | Technology |
|:---|:---|
| REST API | FastAPI 0.110 + Uvicorn |
| Deep Learning | PyTorch 2.2.0 (Apple Silicon MPS) |
| Solar data | SunPy / Fido (JSOC download) |
| Processing | NumPy · SciPy · Astropy (FITS) |
| XAI | Grad-CAM custom hook (stage4.conv) |
| Uncertainty | Monte Carlo Dropout (T=20 passes) |

**Frontend**
| Layer | Technology |
|:---|:---|
| Framework | React 18 + TypeScript |
| Build tool | Vite 6 |
| Styling | Tailwind CSS v4 |
| Charts | Recharts 3.7 |
| Routing | React Router v7 |
| Icons | Lucide React |
| i18n | Custom Context API (EN / ES) |

---

## Quickstart

**Backend**

```bash
cd Auralis
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend**

```bash
cd auralis-front
npm install && npm run dev
```

API: `http://localhost:8000` — Dashboard: `http://localhost:5173`

---

## Repository Layout

```
auralis-back/
├── auralis-back/
│   ├── src/
│   │   ├── api/              FastAPI endpoints (inference, Grad-CAM, metrics)
│   │   ├── ingestion/        JSOC download pipeline
│   │   ├── models/           Coronium V3 PRO architecture, training, inference
│   │   ├── processing/       FITS → normalized tensor (B+/B−, log, Z-score)
│   │   └── experiments/      External benchmarking (ResNet, VGG)
│   └── data/                 raw/ (FITS) and processed/ (NPY + metadata CSV)
├── auralis-front/             React 18 / TypeScript / Vite dashboard
└── requirements.txt
```

---

## Full Research Dossier

> For in-depth technical analysis, scientific rigor, and external benchmarking methodology, see the **[Full Research Dossier](RESEARCH_DOSSIER_MASTER.md)**.

---

## License

Proprietary. All rights reserved.

## Author

**Alejandro C.** — Software Engineer
