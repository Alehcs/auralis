# Auralis

Auralis is a local research/demo system for estimating the current solar activity
index from NASA SDO/HMI magnetograms. It combines an offline data pipeline, a
small convolutional regression model, a FastAPI inference service, and a React
dashboard for inspection, explainability, and experiment review.

This project does not provide operational space-weather forecasts. The promoted
model estimates the activity index for the selected magnetogram in the processed
dataset.

## Objectives

- Train and evaluate a compact magnetogram regression model suitable for CPU
  inference.
- Preserve magnetic polarity information by representing each observation as
  separate B+ and B- channels.
- Serve reproducible local inference, Grad-CAM visualizations, benchmark data,
  and experiment metadata through a single API.
- Provide a dashboard that makes the model behavior inspectable without
  requiring notebook work.

## Current Model

Coronium V3 PRO is a four-stage residual CNN with Efficient Channel Attention
(ECA). The model takes a `(2, 512, 512)` tensor where channel 0 is positive
magnetic polarity and channel 1 is negative magnetic polarity.

| Item | Value |
| --- | --- |
| Promoted checkpoint | `auralis-back/models/best_coronium_v3_pro_augmented.pth` |
| ONNX runtime model | `auralis-back/models/best_coronium_v3_pro.onnx` |
| Parameters | 206,875 |
| ONNX CPU latency | 25.11 ms per image |
| Evaluation run | `exp_005_v3pro_augmented.json` |

### Evaluation Metrics

These values come from the promoted `exp_005` evaluation and are the values used
by the API and dashboard.

| Metric | Value |
| --- | ---: |
| MAE (log-SI) | 0.1048 |
| RMSE (log-SI) | 0.1272 |
| R2 | 0.8634 |
| MAPE | 6.07% |
| Accuracy proxy (`100 - MAPE`) | 93.93% |

The "accuracy" percentage is a derived reporting value, not a classification
accuracy metric.

## Dataset

Processed magnetograms live in `auralis-back/data/processed/` as `.npy` files.
The current curated dataset contains 1,763 HMI Level-1.5 observations covering
Solar Cycles 24 and 25.

Preprocessing converts each magnetogram into a float32 tensor:

1. Load HMI FITS data.
2. Replace invalid limb-mask values with zero.
3. Apply symmetric log scaling: `sign(x) * log(1 + abs(x))`.
4. Split magnetic polarity into B+ and B- channels.
5. Save the result as `(2, 512, 512)`.

The backend still accepts legacy single-channel arrays for compatibility, but
new data should use the dual-channel representation.

## Architecture

```text
NASA JSOC / SDO-HMI
  -> ingestion scripts
  -> preprocessing to dual-channel .npy tensors
  -> Coronium V3 PRO training and ONNX export
  -> FastAPI service
  -> React dashboard
```

The backend is the system boundary for inference and research artifacts. The
frontend does not reimplement model rules; it consumes typed REST responses and
renders the current dataset state.

More detailed architecture notes are in [docs/architecture.md](docs/architecture.md).
Backend script ownership and maintenance notes are in
[docs/backend.md](docs/backend.md).

## Repository Structure

```text
Auralis/
├── auralis-back/
│   ├── src/api/main.py                 # FastAPI service and inference endpoints
│   ├── src/models/train_model.py        # Coronium model, dataset, training loop
│   ├── src/processing/prepare_dataset.py
│   ├── src/ingestion/
│   ├── scripts/                         # Manual evaluation/export utilities
│   ├── models/                          # Checkpoints and ONNX artifacts
│   ├── data/processed/                  # Processed .npy magnetograms
│   └── experiments/                     # Training run metadata
├── auralis-front/
│   ├── src/lib/api.ts                   # REST client boundary
│   ├── src/lib/types.ts                 # Frontend mirrors of API schemas
│   ├── src/features/landing/
│   └── src/features/dashboard/
├── docs/
└── README.md
```

## Technology Stack

Backend:

- FastAPI and Uvicorn
- PyTorch for model definition, training, and Grad-CAM
- ONNX Runtime for dashboard inference
- NumPy, SciPy, Astropy, SunPy, and scikit-image for data processing

Frontend:

- React 18, TypeScript, and Vite
- Tailwind CSS
- Recharts for charts
- Lucide React icons
- shadcn/ui primitives under `src/app/components/ui/`

## Local Development

Run the backend from `auralis-back/`:

```bash
cd auralis-back
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

Run the frontend from `auralis-front/`:

```bash
cd auralis-front
npm install
npm run dev
```

Default URLs:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:5173`

## Environment Variables

| Variable | Used by | Default | Notes |
| --- | --- | --- | --- |
| `VITE_API_URL` | Frontend | `http://localhost:8000` | Base URL for REST calls. |
| `CORS_ORIGINS` | Backend | `http://localhost:5173,http://localhost:5174` | Comma-separated allowed browser origins. |

No internet connection is required to run the local demo once the dataset and
model files are present.

## API Surface

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service and model readiness. |
| `GET` | `/api/stats` | Dataset counts and promoted model metrics. |
| `GET` | `/api/images/list` | Processed `.npy` image catalog. |
| `GET` | `/api/images/{filename}` | Render a magnetogram PNG. |
| `GET` | `/api/predict/{filename}` | ONNX inference for one processed image. |
| `GET` | `/api/explain/{filename}` | Grad-CAM overlay. |
| `GET` | `/api/explain-panels/{filename}` | Three-panel B+ / B- / Grad-CAM figure. |
| `GET` | `/api/benchmark` | Coronium and baseline architecture comparison. |
| `GET` | `/api/experiments` | Training run metadata. |
| `GET` | `/api/polarity-series` | Recent B+ / B- mean flux series. |
| `POST` | `/api/predict-upload` | Black-box inference for uploaded `.npy` files. |

## Important Workflows

### Promote a New Model

1. Train or evaluate the candidate checkpoint.
2. Save the promoted PyTorch weights under `auralis-back/models/`.
3. Export the matching ONNX model.
4. Update frozen metrics in `auralis-back/src/api/main.py`.
5. Update `auralis-front/src/lib/types.ts` only if response schemas changed.
6. Add or update the experiment JSON in `auralis-back/experiments/`.
7. Update this README and `docs/architecture.md` with the new model identity,
   metrics, and any changed assumptions.

### Add a Backend Endpoint

Keep request validation and filesystem access in `src/api/main.py`. Add a
Pydantic response model when the endpoint returns structured data, then mirror
that schema in `auralis-front/src/lib/types.ts` and expose the call through
`auralis-front/src/lib/api.ts`.

### Add a Dashboard View

Use `DashboardPage` as the tab shell. The dashboard should treat the API as the
source of truth for model metrics, classifications, and experiment data. Avoid
duplicating thresholds or model constants in React components.

## Development Notes

- Work on `main`; this repository is not currently using isolated worktrees.
- `landing-hero.tsx` is the active landing hero. The old `hero.tsx` component was
  removed.
- Do not reintroduce a "72 hour forecast" claim. The model estimates the current
  index for the selected magnetogram.
- The dashboard's "Current Solar State" is derived from the most recent `.npy`
  file in the local dataset, not from live NASA telemetry.
- The classification thresholds are calibrated to the current ONNX output range:
  `< 1.41` is Low, `1.41` to `< 1.75` is Medium, and `>= 1.75` is High.
- Grad-CAM uses `stage4.conv` as the default target because it captures the last
  spatial feature map before global pooling.

## Citation

If you reference Auralis or its results, please cite the project. Repository
metadata is provided in [`CITATION.cff`](CITATION.cff) (GitHub renders a
"Cite this repository" button from it).

```bibtex
@software{cornejo_auralis_2026,
  author  = {Cornejo, Alejandro},
  title   = {{Auralis / Coronium V3 PRO: A residual CNN for solar
             activity-index regression from dual-channel HMI/SDO magnetograms}},
  year    = {2026},
  version = {3.3.0},
  note    = {DOI pending Zenodo archival}
}
```

> A citable DOI will be minted from a tagged GitHub release via Zenodo; the
> `doi` field in `CITATION.cff` is left commented until then.

## License

Released under the [MIT License](LICENSE).

## Author

Alejandro Cornejo
