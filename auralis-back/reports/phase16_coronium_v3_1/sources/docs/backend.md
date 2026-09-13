# Backend Maintainer Notes

The audited scientific contract is in [Phase 1](phase1.md). The active release is
**Coronium V3.1**, promoted from Phase 1.5; see [Phase 1.6](phase16.md).
`src/models/active_model.py` identifies the checkpoint, ONNX and metrics. API
startup verifies their hashes against `models/coronium_v3_1_manifest.json`.

The backend is both the API layer for the demo and the research workspace used
to build, evaluate, export, and explain Coronium models. This document maps the
backend files by responsibility so a new contributor can understand which files
are runtime-facing, which are reproducibility scripts, and which are legacy
or diagnostic utilities.

## Runtime-Facing Path

`src/api/main.py` is the only runtime-facing backend entrypoint. It loads the
promoted PyTorch checkpoint for Grad-CAM, creates the ONNX Runtime session for
inference, and exposes the REST API consumed by the React dashboard.

The API owns:

- processed image discovery and rendering,
- ONNX inference and classification,
- Grad-CAM figures,
- XAI faithfulness curves,
- static promoted-run metrics,
- benchmark and experiment metadata,
- upload-based black-box tests.

When a new model is promoted, update this file first, then update the TypeScript
schemas and project documentation.

## Training And Model Code

`src/models/train_model.py` defines the Coronium V3 PRO architecture, dataset,
loss, augmentation strategy, training loop, split persistence, and learning-curve
output. It is the source of truth for checkpoint weight schema. The API imports
`CoroniumV3` from here to avoid architecture drift between training and serving.

Sensitive contracts:

- input tensor shape is `(2, 512, 512)`,
- channel 0 is B+ and channel 1 is B-,
- new validation uses `models/split_indices_phase1_v1.json` (1,051 / 263 unique observations),
- `best_coronium_v3_1.pth` is the promoted checkpoint; V3 files remain historical,
- raw SI pixel percentages are used directly; the historical scaler is not applied.

## Data Processing

`src/processing/prepare_dataset.py` is the canonical preprocessing pipeline for
new V3 PRO data. It loads FITS files, computes the raw activity proxy before
resampling, clips the resized field to ±400 G, divides by 400, and splits B+/B-.
It writes a separate `data/processed_phase1_v1/` dataset with raw SI targets and
explicit date scales; existing files cannot be replaced. Shared model input
conversion lives in `src/processing/model_input.py`.

`src/processing/validate_processed.py` is a lightweight integrity check for the
processed dataset. It is intended for local sanity checks, not for automated
quality gates.

## Ingestion

`src/ingestion/download_solar_data.py` is the small single-date/day downloader.
Use it when validating credentials, JSOC availability, or a short date range.

`src/ingestion/massive_ingest_pipeline.py` is an older large-batch ETL path. It
produced the clipped single-channel representation found in the local data.
Its historical CSV does not record a time scale. Existing CSV dates must not be
reinterpreted or appended to a new schema without versioning.

`scripts/kaggle_auralis_v3pro_dataset_builder.py` is the resumable Kaggle
dataset builder used for long-running JSOC acquisition. It is written to run in
a Kaggle notebook cell with Kaggle Secrets and dataset persistence available.
Its log-scaled tensors are a separate experimental representation, incompatible
with the promoted local checkpoint; this builder was not run in Phase 1.

## Evaluation And Reporting Scripts

`scripts/evaluate_final.py --run-dir <run>` requires a newly trained checkpoint
bound to the corrected split. `--legacy-reproduction` explicitly selects the
contaminated historical split. Both require a fresh output directory; neither
replaces historical `reports/results_comparison.csv`. The active scatter reads the
versioned V3.1 MC CSV under `reports/phase16_coronium_v3_1/`.

`scripts/plot_final_scatter.py` renders the publication-style scatter figure
from `reports/results_comparison.csv`.

`scripts/test_inference.py` compares the original and ExtremeAugmentation
checkpoints on high-activity validation samples. It is a targeted regression
check for the augmentation strategy.

`src/experiments/run_external_baselines.py` trains/evaluates external baselines
such as ResNet-18 and VGG-11. The output JSON
(`experiments/phase1_baselines/<timestamp>/results_benchmarking.json`) stays
separate. The historical `experiments/results_benchmarking.json` is consumed by `/api/benchmark`; the
endpoint's hardcoded fallback values are a static mirror of that file, served
only when it is absent.

These baselines were produced under their own benchmark protocol (this script's
`random_split(seed=42)`, 30 epochs), which is a different partition from the
historical V3 model's persisted `models/split_indices.json`. The two are therefore
not strictly evaluated on the same hold-out set. Do not silently recompute the
baselines to "align" them: only refresh `results_benchmarking.json` when the
benchmark table is intentionally republished, and update the dossier and the
`/api/benchmark` fallback in the same change.

## Explainability

`scripts/explain_model.py` is the standalone Grad-CAM figure generator used for
research artifacts. The API has its own Grad-CAM path for dashboard rendering,
but both should use the same target layer convention.

Default target: `stage4`, or `stage4.conv` in the API path when the raw
convolutional output is needed.

## Export And Inference Utilities

`scripts/export_to_onnx.py` exports the promoted PyTorch checkpoint to ONNX and
benchmarks PyTorch CPU vs ONNX Runtime CPU. The API expects
`models/best_coronium_v3_1.onnx` to be present for dashboard inference.

`scripts/predict.py` loads V3.1 by default in eval mode and shares the corrected
clip400/polarity contract. Grad-CAM scripts also default to V3.1 and versioned
figure names. `scripts/test_inference.py` and the Streamlit app remain historical
diagnostics; they are not V3.1 runtime entrypoints. The export script refuses
to replace an existing graph or external-data sidecar.

`scripts/recalculate_scaler.py` rebuilds `models/target_scaler.json` from the
metadata CSV. Use it only when the target column semantics are clear.

`scripts/extract_test_kit.py` exports demo PNGs for representative normal,
moderate, and extreme samples. It reads the full metadata table rather than only
the validation split so the demo can cover the full activity range.

## Visualization And Notebooks

`src/tools/visualize_tensor.py` compares a raw FITS file with its processed
dual-channel tensor and is useful when debugging preprocessing changes.

`src/visualization/app.py` is a legacy Streamlit app. It remains useful as an
inspection tool, but the React dashboard and FastAPI API are the maintained demo
surface.

`notebooks/` contains notebook helper scripts and notes for exploratory data
inspection. Keep notebook code aligned with the current preprocessing contract
when using it for figures or reports.

## Safe Extension Rules

1. Keep preprocessing, training, ONNX export, and API tensor preparation aligned.
2. Do not update dashboard-facing metrics without adding or updating the
   corresponding experiment JSON.
3. Treat old single-channel scripts as legacy unless explicitly upgraded.
4. Keep JSOC ingestion scripts resumable; long runs will be interrupted.
5. Keep all comments, docstrings, notebook notes, and report strings in English.
