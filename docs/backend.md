# Backend Maintainer Notes

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
- validation uses the persisted split in `models/split_indices.json`,
- `best_coronium_v3_pro_augmented.pth` is the promoted checkpoint,
- `models/target_scaler.json` must match the target transform used by training.

## Data Processing

`src/processing/prepare_dataset.py` is the canonical preprocessing pipeline for
new V3 PRO data. It loads FITS files, computes the raw activity proxy before
resampling, applies symmetric log scaling, splits polarity into B+ and B-, and
writes `.npy` tensors plus `metadata_processed.csv`.

`src/processing/validate_processed.py` is a lightweight integrity check for the
processed dataset. It is intended for local sanity checks, not for automated
quality gates.

## Ingestion

`src/ingestion/download_solar_data.py` is the small single-date/day downloader.
Use it when validating credentials, JSOC availability, or a short date range.

`src/ingestion/massive_ingest_pipeline.py` is an older large-batch ETL path. It
still uses the V2-style clipped single-channel representation internally, so do
not use it as-is to produce new V3 PRO training data without updating the
transform to match `prepare_dataset.py`.

`scripts/kaggle_auralis_v3pro_dataset_builder.py` is the resumable Kaggle
dataset builder used for long-running JSOC acquisition. It is written to run in
a Kaggle notebook cell with Kaggle Secrets and dataset persistence available.

## Evaluation And Reporting Scripts

`scripts/evaluate_final.py` reproduces promoted-run metrics and writes
`reports/results_comparison.csv`, which powers the frontend predicted-vs-actual
scatter plot.

`scripts/plot_final_scatter.py` renders the publication-style scatter figure
from `reports/results_comparison.csv`.

`scripts/test_inference.py` compares the original and ExtremeAugmentation
checkpoints on high-activity validation samples. It is a targeted regression
check for the augmentation strategy.

`src/experiments/run_external_baselines.py` trains/evaluates external baselines
such as ResNet-18 and VGG-11. The output JSON is consumed by `/api/benchmark`.

## Explainability

`scripts/explain_model.py` is the standalone Grad-CAM figure generator used for
research artifacts. The API has its own Grad-CAM path for dashboard rendering,
but both should use the same target layer convention.

Default target: `stage4`, or `stage4.conv` in the API path when the raw
convolutional output is needed.

## Export And Inference Utilities

`scripts/export_to_onnx.py` exports the promoted PyTorch checkpoint to ONNX and
benchmarks PyTorch CPU vs ONNX Runtime CPU. The API expects
`models/best_coronium_v3_pro.onnx` to be present for dashboard inference.

`scripts/predict.py` is a legacy FITS inference CLI. Its preprocessing path is
older than V3 PRO and should not be treated as the serving contract without
bringing it back in sync with `prepare_dataset.py`.

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
