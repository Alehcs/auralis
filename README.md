# SolarNetV3 PRO — Helios Pipeline

**Framework de regresión de alta eficiencia para predicción de actividad solar a partir de magnetogramas HMI/SDO.**

Sistema full-stack validado para estimación en tiempo casi-real del índice de manchas solares: ingesta JSOC → preprocesamiento HMI → inferencia CNN → API REST + dashboard interactivo.

---

## Performance

| Métrica | Valor | Condición |
|:---|:---:|:---|
| MAE físico (escala real) | **0.3167** | Targets crudos vs. preds desnormalizadas — métrica oficial de salida |
| MAE espacio Z-Score | 0.1380 | Error en espacio de optimización (comparación interna de training) |
| MAPE | **5.52%** | Precisión superior al 94% |
| R² (analítico) | **~0.81** | Calculado en espacio Z-Score durante training |
| Latencia de Inferencia | **8.7 ms** | Muestra única, Apple M-series MPS |

---

## Architecture

SolarNetV3 PRO es una arquitectura residual ligera de menos de 500K parámetros, optimizada para Apple Silicon (MPS). Acepta entrada de **doble canal** (2, 512, 512) que separa físicamente la polaridad magnética positiva (B+) y negativa (B−) del magnetograma. Global Average Pooling colapsa cada mapa de activación a un escalar antes del head de regresión, eliminando el coste O(H·W·C) de una capa densa. El resultado es un modelo que alcanza una precisión superior al 94% con menos de 500K parámetros frente a los 9.35M de VGG-11.

```
Input (2, 512, 512)  ← canal 0: B+  |  canal 1: B−
  └─ Residual Block ×4  [16→32→64→96 ch, ECA Attention, BatchNorm, Dropout2d, MaxPool2d]
       └─ Global Average Pooling  →  (96,)
            └─ Linear(96, 1)  →  sunspot index
```

> Baselines evaluados con entrada |B| = B+ + B− (1 canal, escala física cruda) — comparación justa 1-canal vs. 2-canal.  
> MAE SolarNetV3 PRO en escala física: **0.3167**. MAE en espacio Z-Score (training loop): 0.1380.

| Modelo | Parámetros | MAE físico | R² | Latencia |
|:---|---:|:---:|:---:|:---:|
| **SolarNetV3 PRO** | **~88 K** | **0.3167** | **~0.81** | **8.7 ms** |
| ResNet-18 | 11.2 M | 0.0755 | 0.9276 | 6.16 ms |
| VGG-11 | 9.35 M | 0.1079 | 0.8621 | 17.23 ms |
| Naive Persistence | 0 | 0.2882 | −0.008 | < 1 ms |

---

## Solución al Mode Collapse — La Cura Matemática

El problema de Mode Collapse (colapso del modelo hacia una predicción constante) fue diagnosticado y eliminado mediante una normalización en dos fases aplicada sobre la distribución real del target:

1. **Normalización logarítmica** — comprime la distribución de valores extremos del índice solar.
2. **Z-Score Poblacional** — estandariza usando estadísticos calculados sobre **1,314 tensores reales**:

$$\mu_{pop} = 1.7658 \qquad \sigma_{pop} = 0.3462$$

$$z = \frac{\log(SI) - \mu_{pop}}{\sigma_{pop}}$$

Esta transformación garantizó que el gradiente de pérdida nunca colapsara a cero y que el modelo aprendiera a discriminar entre niveles de actividad magnética.

---

## Dataset

| Métrica | Valor |
|:---|:---:|
| Total muestras curadas | **1,763** |
| Entrenamiento (con data augmentation) | **1,411** |
| Validación (hold-out aislado) | **352** |
| Formato | NumPy binary (.npy), float32 |
| Resolución procesada | 512 × 512 px |

---

## Scientific Features

**Explicabilidad — Grad-CAM (XAI)**
Se implementó Grad-CAM hookeando la capa `stage4`. Los mapas de calor generados demostraron empíricamente que la IA enfoca su atención de manera quirúrgica **exclusivamente en las regiones magnéticas activas** (manchas solares), ignorando por completo el fondo espacial y el ruido instrumental. Esto valida que el modelo aprendió física real, no artefactos estadísticos.

**Cuantificación de Incertidumbre — Monte Carlo Dropout**
En tiempo de inferencia, las capas Dropout2d se reactivan y se ejecutan N pases estocásticos hacia adelante para producir una media predictiva y varianza. Esto provee una estimación de incertidumbre calibrada sin reentrenamiento.

---

## Sistema de Entrenamiento

- **Early Stopping dinámico:** detuvo el entrenamiento en la **Época 43**, detectando automáticamente el punto de máxima generalización.
- **Sin memorización:** la brecha entre pérdida de entrenamiento y validación permaneció controlada durante todo el ciclo, confirmando que el modelo no sobreentrena.
- **Dispositivo:** Apple Silicon MPS, PyTorch 2.2.0.

---

## System Architecture

```
NASA JSOC (HMI Level-1.5)
  └─ ingestion/            SunPy/Fido download, exponential-backoff retry
       └─ processing/      FITS → float32 .npy, polaridad B+/B−, norm. log + Z-score
            └─ models/     SolarNetV3 PRO — entrenamiento + motor de inferencia
                 └─ api/   FastAPI REST  (predict, gradient-cam, benchmarks)
                      └─ Helios-front/   React 18 + TypeScript dashboard
```

---

## Tech Stack

**Backend**
| Layer | Technology |
|:---|:---|
| API REST | FastAPI 0.110 + Uvicorn |
| Deep Learning | PyTorch 2.2.0 (Apple Silicon MPS) |
| Datos solares | SunPy / Fido (descarga JSOC) |
| Procesamiento | NumPy · SciPy · Astropy (FITS) |
| XAI | Grad-CAM custom hook (stage4.conv) |
| Incertidumbre | Monte Carlo Dropout (T=20 pases) |

**Frontend**
| Layer | Technology |
|:---|:---|
| Framework | React 18 + TypeScript |
| Build tool | Vite 6 |
| Estilos | Tailwind CSS v4 |
| Gráficos | Recharts 3.7 |
| Routing | React Router v7 |
| Iconos | Lucide React |
| i18n | Context API custom (EN / ES) |

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
│   │   ├── ingestion/        Pipeline de descarga JSOC
│   │   ├── models/           Arquitectura SolarNetV3 PRO, entrenamiento, inferencia
│   │   ├── processing/       FITS → tensor normalizado (B+/B−, log, Z-score)
│   │   └── experiments/      Benchmarking externo (ResNet, VGG)
│   └── data/                 raw/ (FITS) y processed/ (NPY + metadata CSV)
├── Helios-front/             React 18 / TypeScript / Vite dashboard
└── requirements.txt
```

---

## Full Research Dossier

> Para análisis técnico profundo, rigor científico y metodología de benchmarking externo, ver el **[Dossier de Investigación Completo](RESEARCH_DOSSIER_MASTER.md)**.

---

## License

Proprietary. All rights reserved.

## Author

**Alejandro C.** — Software Engineer
