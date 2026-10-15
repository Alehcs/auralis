# Auralis

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20620546-blue)](https://doi.org/10.5281/zenodo.20620546)

Auralis estimates the current solar activity index from NASA SDO/HMI
magnetograms. It combines a data pipeline, a compact CNN (Coronium), a FastAPI
inference service and a React dashboard with Grad-CAM explainability.

It estimates the index for a given magnetogram; it does not forecast future
activity or space weather.

## Model

**Coronium V3.2** — residual CNN with Efficient Channel Attention, 206,875
parameters, served as a self-contained ONNX model on CPU.

- **Input:** `(2, 512, 512)` float32 with separate B+ / B− channels, from
  `clip(B_LOS, ±400 G) / 400`.
- **Target:** percentage of pixels with `|B_LOS| > 200 G`.

| Metric | Value |
| --- | ---: |
| MAE (SI pp) | 0.0483 |
| RMSE (SI pp) | 0.0591 |
| R² | 0.9714 |
| MAPE | 2.91% |

These metrics come from 263 validation observations that were also used to
select the checkpoint, so they are not an independent test. Performance on
low-activity cases is weaker. The `uncertainty` returned by the API is a
heuristic from input-noise sensitivity, not a calibrated probability.

Set `AURALIS_RELEASE=3.1` to run the previous V3.1 release instead.

## Dataset

The dataset has 1,314 processed magnetograms (`auralis-back/data/processed/`, `.npy`)
covering 2016-02-03 to 2026-04-12. The training and validation split
(1,051 / 263) has no overlap.

## Architecture

```text
SDO/HMI → preprocessing (B+ / B− tensors) → Coronium (PyTorch → ONNX) → FastAPI → React dashboard
```

```text
auralis-back/    FastAPI API, model, training, data and experiments
auralis-front/   React + TypeScript + Vite dashboard
prototypes/      Solar 3D / AR viewer used by the Simulation tab
```

## Quick start

Backend:

```bash
cd auralis-back
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

Frontend:

```bash
cd auralis-front
npm install
npm run dev
```

The API runs at `http://localhost:8000` and the dashboard at
`http://localhost:5173`. No internet connection is needed once the data and
model files are present.

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000` | API base URL for the frontend |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174` | Allowed browser origins |

## Main endpoints

| Route | Purpose |
| --- | --- |
| `GET /health` | Service and model status |
| `GET /api/stats` | Dataset counts and model metrics |
| `GET /api/images/list` | Magnetogram catalog |
| `GET /api/predict/{filename}` | Activity index for one magnetogram |
| `GET /api/explain/{filename}` | Grad-CAM overlay |
| `POST /api/predict-upload` | Prediction for an uploaded `.npy` file |

## Citation

See [`CITATION.cff`](CITATION.cff) or the archived release:
https://doi.org/10.5281/zenodo.20620546

```bibtex
@software{cornejo_auralis_2026,
  author  = {Cornejo, Alejandro},
  title   = {{Auralis / Coronium V3 PRO: A residual CNN for solar
             activity-index regression from dual-channel HMI/SDO magnetograms}},
  year    = {2026},
  version = {3.3.0},
  doi     = {10.5281/zenodo.20620546},
  url     = {https://doi.org/10.5281/zenodo.20620546}
}
```

## License

MIT — see [LICENSE](LICENSE). Author: Alejandro Cornejo.
