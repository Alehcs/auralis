/**
 * Shared TypeScript type definitions for all Auralis REST API responses.
 *
 * Each interface mirrors the corresponding Pydantic schema in
 * `auralis-back/src/api/main.py` and must be kept in sync when
 * server-side schemas change.
 */

// ---------------------------------------------------------------------------
// Images
// ---------------------------------------------------------------------------

/** Metadata record for a single processed HMI magnetogram file. */
export interface ImageListItem {
    /** Basename of the `.npy` file, e.g. `hmi.m_45s.2023.01.15_00_00_00_TAI.npy`. */
    filename: string;
    /** UTC timestamp parsed from the filename (`YYYY-MM-DDTHH:MM:SSZ`), or `null` if unparseable. */
    date: string | null;
    /** File size in bytes on disk. */
    size_bytes: number;
}

/** Paginated response for the `/api/images/list` endpoint. */
export interface ImageListResponse {
    /** All available magnetogram records, sorted by date descending. */
    images: ImageListItem[];
    /** Total number of `.npy` files in `data/processed/`. */
    total: number;
}

// ---------------------------------------------------------------------------
// Prediction
// ---------------------------------------------------------------------------

/**
 * Solar activity classification derived from the predicted sunspot index.
 *
 * Thresholds follow the GOES X-ray scale adapted to the V3 PRO normalised range:
 * - `< 1.6`      → Low  / C-class / #22c55e
 * - `1.6 – <2.0` → Medium / M-class / #f97316
 * - `≥ 2.0`      → High / X-class / #ef4444
 */
export interface ClassificationInfo {
    /** "Low" | "Medium" | "High" */
    level: 'Low' | 'Medium' | 'High';
    /** Human-readable label, e.g. "Bajo / Actividad Normal" */
    label: string;
    /** GOES flare class letter: "C" | "M" | "X" */
    flare_class: string;
    /** Hex colour for UI rendering, e.g. "#22c55e" */
    hex_color: string;
}

/**
 * Solar activity regression result from a single Coronium inference call.
 *
 * `uncertainty` is the standard deviation across 20 Monte Carlo Dropout
 * stochastic forward passes. `confidence` is a heuristic inversely
 * proportional to the absolute magnitude of `sunspot_index`.
 */
export interface PredictionResult {
    /** Predicted sunspot index (continuous, normalised to the training distribution). */
    sunspot_index: number;
    /** Three-tier activity level derived from `classification.level`. */
    risk_level: 'Low' | 'Medium' | 'High';
    /** Prediction confidence in `[0.75, 0.99]`; conservative for high-activity events. */
    confidence: number;
    /** Empirical uncertainty: std-dev of 20 MC Dropout passes. */
    uncertainty: number;
    /** Full classification object with label, flare class, and hex colour. */
    classification: ClassificationInfo;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

/**
 * Dataset-level statistics and frozen training performance metrics.
 *
 * `mae`, `rmse`, and `r2_score` are hardcoded from the final `exp_003`
 * training run and must be updated manually when a new model is promoted.
 */
export interface SystemStats {
    /** Count of `.npy` files currently in `data/processed/`. */
    total_images: number;
    /** Aggregate disk footprint of all magnetogram files in MiB. */
    disk_usage_mb: number;
    /** Mean Absolute Error on the `exp_003` validation set. */
    mae: number;
    /** Root Mean Squared Error on the `exp_003` validation set. */
    rmse: number;
    /** Coefficient of determination (R²) on the `exp_003` validation set. */
    r2_score: number;
    /** UTC ISO-8601 timestamp of the most recently modified `.npy` file. */
    last_updated: string;
}

// ---------------------------------------------------------------------------
// Logs
// ---------------------------------------------------------------------------

/** Trailing log lines from a single `.log` file in the project root. */
export interface LogEntry {
    /** Log filename, e.g. `training_v3_pro.log`. */
    filename: string;
    /** Last 50 lines of the file, stripped of trailing newlines. */
    lines: string[];
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

/** API liveness probe response. */
export interface HealthResponse {
    /** Liveness indicator; `"ok"` when the server is operational. */
    status: string;
    /** Semantic version string of the running API, e.g. `"2.1.0"`. */
    version: string;
}

// ---------------------------------------------------------------------------
// XAI Faithfulness
// ---------------------------------------------------------------------------

/**
 * Single data point on the Grad-CAM faithfulness degradation curve.
 *
 * At each threshold, the `pixels_removed_pct` most salient pixels
 * (by Grad-CAM importance) are zeroed out and the model is re-evaluated.
 * A parallel random-masking baseline is computed for comparison.
 */
export interface XAIPoint {
    /** Percentage of total pixels masked at this threshold step (0–100, step 10). */
    pixels_removed_pct: number;
    /** Model prediction after Grad-CAM-ordered pixel removal. */
    prediction: number;
    /** `prediction` normalised to the unmasked baseline (1.0 = no change). */
    normalized: number;
    /** Model prediction after random-ordered pixel removal (control). */
    random_prediction: number;
    /** `random_prediction` normalised to the unmasked baseline. */
    random_normalized: number;
}

/**
 * Complete Grad-CAM faithfulness evaluation for one magnetogram.
 *
 * `auc_score` = (∫random − ∫GradCAM) / 100 over the masking range [0, 100].
 * Positive values indicate that the Grad-CAM saliency map identifies
 * genuinely predictive pixels (faithful saliency).
 */
export interface XAIFaithfulnessResult {
    /** Source magnetogram filename. */
    filename: string;
    /** Unmasked model prediction used as the normalisation reference. */
    baseline_prediction: number;
    /** Degradation curve sampled at 10-percentage-point masking thresholds. */
    curve: XAIPoint[];
    /** Faithfulness score; higher is more faithful. Typical range: [−0.1, 0.3]. */
    auc_score: number;
}

// ---------------------------------------------------------------------------
// Benchmark
// ---------------------------------------------------------------------------

/** Per-model performance and efficiency profile from the benchmarking run. */
export interface ModelBenchmark {
    /** Human-readable model identifier, e.g. `"ResNet18 (Baseline)"`. */
    name: string;
    /** Total number of trainable parameters. */
    parameters: number;
    /** Mean Absolute Error on the validation set. */
    mae: number;
    /** Root Mean Squared Error on the validation set. */
    rmse: number;
    /** Coefficient of determination (R²) on the validation set. */
    r2_score: number;
    /** Mean single-sample inference latency in milliseconds. */
    inference_ms: number;
}

/**
 * Architecture comparison: baseline models vs. Coronium V3 PRO.
 *
 * `mae_reduction_pct` and `rmse_reduction_pct` express the relative
 * improvement of `proposed` over `baseline` as positive percentages.
 */
export interface BenchmarkResult {
    /** ResNet-18 baseline metrics. */
    baseline: ModelBenchmark;
    /** Coronium V3 PRO metrics (the proposed architecture). */
    proposed: ModelBenchmark;
    /** VGG-11 baseline metrics; `null` when the benchmarking JSON is absent. */
    vgg11?: ModelBenchmark | null;
    /** MAE reduction of `proposed` vs `baseline` in percent. */
    mae_reduction_pct: number;
    /** RMSE reduction of `proposed` vs `baseline` in percent. */
    rmse_reduction_pct: number;
}

// ---------------------------------------------------------------------------
// Experiments
// ---------------------------------------------------------------------------

/** Training hyperparameters recorded in an experiment run JSON. */
export interface ExperimentHyperparams {
    learning_rate: number;
    dropout_rate: number;
    seed: number;
    batch_size: number;
    optimizer: string;
    scheduler: string;
    max_epochs: number;
    early_stopping_patience: number;
    /** Actual number of epochs completed (may be less than `max_epochs` due to early stopping). */
    epochs_run: number;
}

/** Validation metrics captured at the end of a training run. */
export interface ExperimentMetrics {
    final_mae: number;
    final_rmse: number;
    r2_score: number;
    /** Epoch index at which the best validation loss was achieved. */
    best_epoch: number;
    best_val_loss: number;
}

/** Dataset partition sizes and augmentation flag for a training run. */
export interface ExperimentDataset {
    total_samples: number;
    train_samples: number;
    val_samples: number;
    /** Whether online data augmentation was active during training. */
    augmentation: boolean;
}

/** Hardware and software environment captured at training time. */
export interface ExperimentEnvironment {
    device: string;
    framework: string;
    python_version: string;
    os: string;
}

/** Full metadata record for a single experiment run. */
export interface ExperimentEntry {
    /** Unique run identifier, e.g. `"exp_003"`. */
    run_id: string;
    run_name: string;
    /** ISO-8601 UTC timestamp of the run start. */
    date: string;
    model_name: string;
    weights_file: string;
    hyperparameters: ExperimentHyperparams;
    dataset: ExperimentDataset;
    metrics: ExperimentMetrics;
    environment: ExperimentEnvironment;
    notes: string;
    /** Basename of the source JSON file within `experiments/`. */
    metadata_file: string;
}

// ---------------------------------------------------------------------------
// AIA 193Å / Dual Channel
// ---------------------------------------------------------------------------

/**
 * Inference result from the dual-channel CoroniumDual endpoint.
 *
 * Extends {@link PredictionResult} with the active inference mode. When
 * `coronium_v3_dual.pth` weights are unavailable, the backend silently falls
 * back to single-channel inference and sets `dual_channel = false`.
 */
export interface DualChannelPredictionResult extends PredictionResult {
    /** `true` when CoroniumDual (2-channel) weights were used; `false` on fallback. */
    dual_channel: boolean;
    /** Fixed ordered tuple describing the channel stack. */
    channels: ['hmi_magnetogram', 'aia_193'];
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

/** Structured error payload returned by the API on non-2xx responses. */
export interface ApiError {
    error: string;
    message: string;
    status: number;
}
