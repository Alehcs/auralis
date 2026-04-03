# SolarNet V2 PRO — Helios Pipeline

**High-efficiency regression framework for solar activity forecasting using HMI/SDO magnetograms.**

A full-stack system for near-real-time sunspot index estimation: JSOC data ingestion → HMI magnetogram preprocessing → CNN inference → REST API + interactive dashboard.

---

## Performance

| Metric | Value | Condition |
|:---|:---:|:---|
| Validation MAE | **0.1416** | Hold-out set, 1,158 magnetograms |
| R² Score | **0.8705** | Hold-out set |
| Inference Latency | **8.7 ms** | Single sample, Apple M-series MPS |

---

## Architecture

SolarNet is a four-block convolutional regressor with Global Average Pooling. GAP collapses each feature map to a single scalar before the regression head, eliminating the O(H·W·C) parameter cost of a dense classification layer. The result is a model that reaches **95.3% of VGG-11's regression performance with 4.2% of its parameters (389 K vs. 9.35 M)**.

```
Input (1, 512, 512)
  └─ Conv Block ×4  [32→64→128→256 ch, BatchNorm, Dropout2d, MaxPool2d]
       └─ Global Average Pooling  →  (256,)
            └─ Linear(256, 1)  →  sunspot index
```

| Model | Params | Val MAE | Val R² | Latency |
|:---|---:|:---:|:---:|:---:|
| **SolarNet V2 PRO** | **389 K** | **0.1416** | **0.8705** | **8.7 ms** |
| VGG-11 | 9.35 M | 0.1326 | 0.9137 | 31.4 ms |
| ResNet-18 | 11.2 M | 0.1589 | 0.8201 | 12.1 ms |
| Naive Persistence | 0 | 0.4823 | 0.0000 | < 1 ms |

---

## Scientific Features

**Explainability — Grad-CAM**
Class Activation Maps are computed over the final convolutional layer to produce saliency overlays on the magnetogram. This allows visual verification that the model attends to active-region flux concentrations rather than instrument artefacts or limb effects.

**Uncertainty Quantification — Monte Carlo Dropout**
At inference time, Dropout2d layers are reactivated and N stochastic forward passes are aggregated to produce a predictive mean and variance. This provides a principled, calibration-free uncertainty estimate without retraining.

---

## System Architecture

```
NASA JSOC (HMI Level-1.5)
  └─ ingestion/            SunPy/Fido download, exponential-backoff retry
       └─ processing/      FITS → float32 .npy, ±400 G clip, [-1, 1] norm
            └─ models/     SolarNet training + inference engine
                 └─ api/   FastAPI REST  (predict, gradient-cam, benchmarks)
                      └─ Helios-front/   React 18 + TypeScript dashboard
```

---

## Quickstart

**Backend**

```bash
cd HeliosPipeline
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend**

```bash
cd Helios-front
npm install && npm run dev
```

API: `http://localhost:8000` — Dashboard: `http://localhost:5173`

---

## Repository Layout

```
Helios-Pipeline/
├── HeliosPipeline/
│   ├── src/
│   │   ├── api/              FastAPI endpoints (inference, Grad-CAM, metrics)
│   │   ├── ingestion/        JSOC download pipeline
│   │   ├── models/           SolarNet architecture, training, inference
│   │   ├── processing/       FITS → normalised tensor pipeline
│   │   └── experiments/      External baseline benchmarking (ResNet, VGG)
│   └── data/                 raw/ (FITS) and processed/ (NPY + metadata CSV)
├── Helios-front/             React 18 / TypeScript / Vite dashboard
└── requirements.txt
```

---

## Full Research Dossier

> For deep technical analysis, scientific rigour, and external benchmarking methodology, see the **[Full Research Dossier](RESEARCH_DOSSIER_MASTER.md)**.

---

## License

Proprietary. All rights reserved.

## Author

**Alejandro C.** — Software Engineer
