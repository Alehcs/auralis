/**
 * Type definitions for HeliosPipeline API responses.
 */

// -- Images ----------------------------------------------------------------

export interface ImageListItem {
    filename: string;
    date: string | null;
    size_bytes: number;
}

export interface ImageListResponse {
    images: ImageListItem[];
    total: number;
}

// -- Prediction ------------------------------------------------------------

export interface PredictionResult {
    sunspot_index: number;
    risk_level: 'Low' | 'Medium' | 'High';
    confidence: number;
    uncertainty: number;
}

// -- Stats -----------------------------------------------------------------

export interface SystemStats {
    total_images: number;
    disk_usage_mb: number;
    mae: number;
    rmse: number;
    r2_score: number;
    last_updated: string;
}

// -- Logs ------------------------------------------------------------------

export interface LogEntry {
    filename: string;
    lines: string[];
}

// -- Health ----------------------------------------------------------------

export interface HealthResponse {
    status: string;
    version: string;
}

// -- XAI Faithfulness ------------------------------------------------------

export interface XAIPoint {
    pixels_removed_pct: number;
    prediction: number;
    normalized: number;
    random_prediction: number;
    random_normalized: number;
}

export interface XAIFaithfulnessResult {
    filename: string;
    baseline_prediction: number;
    curve: XAIPoint[];
    auc_score: number;
}

// -- Benchmark -------------------------------------------------------------

export interface ModelBenchmark {
    name: string;
    parameters: number;
    mae: number;
    rmse: number;
    r2_score: number;
    inference_ms: number;
}

export interface BenchmarkResult {
    baseline: ModelBenchmark;
    proposed: ModelBenchmark;
    mae_reduction_pct: number;
    rmse_reduction_pct: number;
}

// -- Experiments -----------------------------------------------------------

export interface ExperimentHyperparams {
    learning_rate: number;
    dropout_rate: number;
    seed: number;
    batch_size: number;
    optimizer: string;
    scheduler: string;
    max_epochs: number;
    early_stopping_patience: number;
    epochs_run: number;
}

export interface ExperimentMetrics {
    final_mae: number;
    final_rmse: number;
    r2_score: number;
    best_epoch: number;
    best_val_loss: number;
}

export interface ExperimentDataset {
    total_samples: number;
    train_samples: number;
    val_samples: number;
    augmentation: boolean;
}

export interface ExperimentEnvironment {
    device: string;
    framework: string;
    python_version: string;
    os: string;
}

export interface ExperimentEntry {
    run_id: string;
    run_name: string;
    date: string;
    model_name: string;
    weights_file: string;
    hyperparameters: ExperimentHyperparams;
    dataset: ExperimentDataset;
    metrics: ExperimentMetrics;
    environment: ExperimentEnvironment;
    notes: string;
    metadata_file: string;
}

// -- AIA 193Å / Dual Channel -----------------------------------------------

/**
 * Dual-channel prediction result from SolarNetDual.
 * Extends PredictionResult with metadata about the inference mode.
 * When dual-channel weights are not yet trained, the backend falls back
 * to single-channel and sets dual_channel = false.
 */
export interface DualChannelPredictionResult extends PredictionResult {
    dual_channel: boolean;
    channels: ['hmi_magnetogram', 'aia_193'];
}

// -- Errors ----------------------------------------------------------------

export interface ApiError {
    error: string;
    message: string;
    status: number;
}
