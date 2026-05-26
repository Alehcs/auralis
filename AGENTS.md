# Auralis - Context for Codex

Read this at the start of each session. Update it when routes, model artifacts,
metrics, or important conventions change.

## Project Summary

Auralis is a machine-learning pipeline for estimating the current solar activity
index from NASA SDO/HMI magnetograms. It is an academic and technical demo, not
a production service with real users.

## Repository Layout

```text
/Users/alejandro/Documents/ProyectosAG/Auralis/
├── auralis-front/     # React + Vite + TypeScript + Tailwind
└── auralis-back/      # FastAPI + PyTorch + ONNX Runtime
```

## Backend (`auralis-back/`)

- Entrypoint: `src/api/main.py`
- Run command: `uvicorn src.api.main:app --reload`
- Working directory: `auralis-back/`
- Port: `8000`

### Model

- Coronium V3 PRO: residual CNN with ECA Attention and dual-channel B+ / B- input.
- Checkpoint: `models/best_coronium_v3_pro_augmented.pth`
- ONNX: `models/best_coronium_v3_pro.onnx`
- Parameters: 206,875
- ONNX inference: 25.11 ms per image on CPU
- The model does not forecast future activity. It estimates the current index
  for the selected magnetogram.

### Promoted Metrics (`exp_005`)

| Metric | Value |
| --- | ---: |
| MAE (log-SI) | 0.1076 |
| RMSE (log-SI) | 0.1284 |
| R2 | 0.8608 |
| MAPE | 6.22% |
| Accuracy proxy (`100 - MAPE`) | 93.78% |

The 93.78% value is the only supported accuracy-style percentage in the UI.

### Dataset

- 1,763 `.npy` images in `data/processed/`
- Source: HMI Level-1.5, 512 x 512
- Coverage: 2011-2025, Solar Cycles 24-25
- Preprocessing: symmetric log scale plus B+ / B- split into `(2, H, W)`

### Activity Classification

| Index | Level | Class |
| ---: | --- | --- |
| `< 1.41` | Low | C |
| `1.41` to `< 1.75` | Medium | M |
| `>= 1.75` | High | X |

### Main Endpoints

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API and model status. |
| `GET` | `/api/stats` | Dataset stats and promoted metrics. |
| `GET` | `/api/images/list` | Processed `.npy` catalog. |
| `GET` | `/api/images/{filename}` | Render magnetogram PNG. |
| `GET` | `/api/predict/{filename}` | ONNX inference. |
| `GET` | `/api/explain/{filename}` | Grad-CAM overlay. |
| `GET` | `/api/benchmark` | ResNet18 vs Coronium comparison. |
| `GET` | `/api/experiments` | Training run history. |
| `GET` | `/api/polarity-series` | B+ / B- time series. |

## Frontend (`auralis-front/`)

- Run command: `npm run dev`
- Working directory: `auralis-front/`
- Port: `5173`
- API base: `http://localhost:8000`
- Environment override: `VITE_API_URL`

### Stack

- React 18 + TypeScript + Vite
- Tailwind CSS, dark theme based on `bg-neutral-950`
- Framer Motion, Recharts, Lucide icons
- shadcn/ui components under `src/app/components/ui/`

### Routes

| Route | Component | Purpose |
| --- | --- | --- |
| `/` | `LandingPage` | Hero, overview, project summary, CTA. |
| `/dashboard` | `DashboardPage` | Main tabbed dashboard. |

### Key Files

```text
src/
├── app/App.tsx
├── lib/api.ts
├── lib/types.ts
├── components/
│   ├── shared/ripple-button.tsx
│   └── figma/ImageWithFallback.tsx
├── features/landing/
│   ├── landing-hero.tsx
│   ├── landing-page.tsx
│   ├── system-overview.tsx
│   ├── architecture-diagram.tsx
│   ├── project-description.tsx
│   └── landing-cta.tsx
└── features/dashboard/
    ├── dashboard-page.tsx
    ├── scientific-header.tsx
    ├── scientific-sidebar.tsx
    ├── magnetogram-panel.tsx
    ├── model-metrics.tsx
    ├── execution-logs.tsx
    ├── prediction-chart.tsx
    ├── pages/research-insights.tsx
    └── components/
        ├── global-metrics.tsx
        ├── predicted-vs-actual.tsx
        ├── xai-faithfulness.tsx
        ├── architecture-comparison.tsx
        ├── config-panel.tsx
        ├── experiment-log.tsx
        └── kfold-results.tsx
```

### Assets

- `public/sun.gif`: NASA space sun GIF used in the landing hero.
- `public/solar-storm.gif`: alternate NASA solar storm GIF, currently inactive.

## Backend Code Structure

```text
src/
├── api/main.py
├── models/train_model.py
├── experiments/run_external_baselines.py
├── ingestion/
├── processing/
├── tools/visualize_tensor.py
└── visualization/app.py

scripts/
├── kaggle_auralis_v3pro_dataset_builder.py
├── evaluate_final.py
├── explain_model.py
├── export_to_onnx.py
├── predict.py
├── test_inference.py
├── recalculate_scaler.py
├── extract_test_kit.py
└── plot_final_scatter.py
```

## Conventions

- Work on `main`; do not create isolated worktrees for this project.
- `landing-hero.tsx` is the active landing hero. `hero.tsx` was removed.
- Do not reintroduce "Forecast: 72 hours"; the current model does not support
  that claim.
- The dashboard's "Current Solar State" is based on the latest local `.npy`
  file, not live NASA telemetry.
- The app can run fully on localhost after data and model artifacts are present.

## When to Update This File

Update `/Users/alejandro/Documents/ProyectosAG/Auralis/AGENTS.md` when:

- Routes or key components change.
- Endpoints are added or removed.
- Promoted model metrics change.
- A new checkpoint or ONNX artifact is promoted.
