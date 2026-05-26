# Auralis Architecture Notes

This document is for developers extending the project. It focuses on system
boundaries, data contracts, and the parts that are easiest to break by accident.

## System Boundary

Auralis is split into two applications:

- `auralis-back/`: owns data loading, model inference, Grad-CAM, static research
  metrics, and experiment metadata.
- `auralis-front/`: owns routing, UI state, charts, and presentation of API
  responses.

The frontend should not duplicate model behavior. Thresholds, metric values,
and prediction semantics belong in the backend response models. React components
may format those values, but they should not reinterpret them.

## Data Flow

```text
FITS magnetogram
  -> prepare_dataset.py
  -> .npy tensor (2, 512, 512)
  -> FastAPI loads tensor
  -> ONNX Runtime returns scalar activity index
  -> backend classifies scalar
  -> frontend renders prediction and supporting figures
```

The dual-channel tensor is the main data contract between processing, training,
and inference:

- channel 0: `B+ = max(log_scaled_flux, 0)`
- channel 1: `B- = max(-log_scaled_flux, 0)`

Keeping the two polarities separate is intentional. Reconstructing a single
signed magnetogram is useful for display, but the model expects the channels as
separate input features.

## Backend Responsibilities

`src/api/main.py` is intentionally broad because this project has one local API
entrypoint. It handles:

- service startup and model loading,
- ONNX Runtime session management,
- processed image catalog and rendering,
- prediction and classification,
- Grad-CAM rendering,
- XAI faithfulness curves,
- benchmark and experiment metadata,
- upload-based black-box tests.

Model files are loaded once at startup. Prediction results and XAI faithfulness
results are cached in memory by filename because repeated dashboard visits often
ask for the same expensive outputs.

## Inference Path

The primary dashboard inference path uses ONNX Runtime:

1. Load `.npy`.
2. Normalize legacy single-channel data if needed.
3. Expand to `(1, 2, H, W)`.
4. Run 20 noisy ONNX passes.
5. Return the mean prediction and standard deviation.

The ONNX graph was exported in eval mode, so dropout is not active at runtime.
The uncertainty value is therefore an input-noise simulation, not true MC
Dropout. Keep that distinction clear in documentation and UI copy.

PyTorch remains loaded for Grad-CAM because saliency requires autograd hooks.

## Classification Thresholds

The current thresholds are calibrated to the promoted ONNX model's observed
output range:

| Prediction | Level | Class |
| ---: | --- | --- |
| `< 1.41` | Low | C |
| `1.41` to `< 1.75` | Medium | M |
| `>= 1.75` | High | X |

These thresholds are not universal solar physics constants. Recalibrate them
when a new model, target transform, or broader solar-cycle dataset is promoted.

## Frontend Responsibilities

`src/lib/api.ts` is the REST boundary. Components should call it instead of
building fetch requests inline.

`src/lib/types.ts` mirrors the backend Pydantic models. When an API response
changes, update the Pydantic schema, the TypeScript interface, and the API
client in the same change.

`DashboardPage` is a tab shell. The major dashboard tabs are:

- `overview`: model metrics and current dataset-derived state,
- `monitoring`: magnetogram/AIA view, prediction, Grad-CAM, upload test,
- `pipeline`: prediction charts,
- `research`: experiment and evaluation views,
- `logs`: local log tails,
- `config`: demo settings panel.

The "Current Solar State" panel is derived from the most recent local `.npy`
file. It is not a live NASA feed.

## Sensitive Areas

- Preprocessing must stay aligned between `prepare_dataset.py`, API tensor
  preparation, and ONNX export. Small changes here create distribution shift.
- Do not change the filename parsing pattern without checking image sorting,
  latest-image selection, and polarity time-series charts.
- Grad-CAM hooks must be removed after each run. Accumulated hooks will cause
  repeated callbacks and unnecessary memory growth.
- Upload endpoints accept arbitrary `.npy` files. Keep validation strict and do
  not add path-based access for uploads.
- Static metrics in `/api/stats` and `/api/benchmark` are promoted-run metadata.
  Update them only when a new run is accepted as the reference model.

## Extension Checklist

When extending the project, check the following before merging:

1. Does the change alter the tensor shape, target transform, or model output
   range? If yes, update preprocessing, inference, docs, and thresholds together.
2. Does the API response shape change? If yes, update Pydantic schemas,
   TypeScript interfaces, and frontend call sites in one change.
3. Does the UI make a claim about time, forecasting, accuracy, or live data?
   Confirm the backend can actually support that claim.
4. Does the feature depend on files under `data/`, `models/`, `reports/`, or
   `experiments/`? Document the required artifact and failure mode.
5. Is the result expensive to compute? Consider filename-keyed caching and a
   cache invalidation note.
