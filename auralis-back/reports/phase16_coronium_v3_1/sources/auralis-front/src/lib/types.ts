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
    /** UTC timestamp explicitly converted from the filename’s TAI record time (`YYYY-MM-DDTHH:MM:SSZ`), or `null` if unparseable. */
    date: string | null;
    date_original?: string | null;
    date_scale?: string | null;
    date_source?: string;
    date_utc?: string | null;
    aia_source?: 'synthetic_hmi_proxy' | 'local_aia_file_unverified';
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
 * Historical demo thresholds retained for V3.1; not calibrated or GOES classes:
 * - `< 1.41`        -> Low    / C-class / #22c55e
 * - `1.41 - <1.75` -> Medium / M-class / #f97316
 * - `>= 1.75`      -> High   / X-class / #ef4444
 */
export interface ClassificationInfo {
    /** "Low" | "Medium" | "High" */
    level: 'Low' | 'Medium' | 'High';
    /** Human-readable label, e.g. "Low / Normal Activity" */
    label: string;
    /** Legacy activity-band symbol; not validated against GOES flare classes. */
    flare_class: string;
    /** Hex colour for UI rendering, e.g. "#22c55e" */
    hex_color: string;
}

/**
 * Solar activity regression result from a single Coronium inference call.
 *
 * The current ONNX endpoint reports uncertainty as the standard deviation
 * across 20 input-noise passes. The exported ONNX graph is eval-mode, so this
 * is not true dropout-based uncertainty.
 */
export interface PredictionResult {
    model_name: string;
    model_version: string;
    /** Predicted raw SI pixel percentage; no logarithm or Z-score. */
    input_contract?: string;
    target_contract?: string;
    output_units?: string;
    model_status?: string;
    prediction_method?: string;
    confidence_method?: string;
    uncertainty_method?: string;
    sunspot_index: number;
    /** Three-tier activity level derived from `classification.level`. */
    risk_level: 'Low' | 'Medium' | 'High';
    /** Heuristic score in `[0.75, 0.99]`; not a calibrated probability. */
    confidence: number;
    /** Empirical uncertainty: std-dev of 20 ONNX input-noise passes. */
    uncertainty: number;
    /** Full classification object with label, legacy band symbol, and hex colour. */
    classification: ClassificationInfo;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

/**
 * Dataset-level statistics and frozen evaluation performance metrics.
 *
 * Official V3.1 MC Dropout T=20 metrics on 263 clean validation observations
 * used for checkpoint selection; not an independent or temporal test.
 * Single-pass serving metrics and historical V3 are separate fields.
 */
export interface SystemStats {
    model_name: string;
    model_version: string;
    mape: number;
    evaluation_protocol: string;
    validation_observations: number;
    observation_overlap: number;
    serving_deterministic: { protocol: string; pytorch: Record<string, number>; onnx: Record<string, number> };
    historical_v3: { model_name: string; status: string; source: string; validation_rows: number; observation_overlap: number; metrics: Record<string, number> };
    /** Count of `.npy` files currently in `data/processed/`. */
    total_images: number;
    /** Aggregate disk footprint of all magnetogram files in MiB. */
    disk_usage_mb: number;
    /** Mean Absolute Error in raw SI space (percentage points for errors), MC Dropout T=20, 263 clean selection-validation observations. */
    mae: number;
    /** Root Mean Squared Error — raw SI space (percentage points for errors), same evaluation protocol as `mae`. */
    rmse: number;
    /** R2 on clean validation used for model selection. */
    r2_score: number;
    /** UTC ISO-8601 timestamp of the most recently modified `.npy` file. */
    metrics_status?: string;
    metric_units?: string;
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
    /** Semantic version string of the running API, e.g. `"3.0.0"`. */
    version: string;
    /** True when both the PyTorch checkpoint and ONNX session are ready. */
    model_loaded: boolean;
    /** Backend selected for PyTorch Grad-CAM work (`mps`, `cuda`, or `cpu`). */
    device: string;
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
 * Historical response shape for the early AIA/HMI dual-input experiment.
 *
 * The current `/api/predict-dual/{filename}` endpoint returns `PredictionResult`
 * and uses the same B+ / B- Coronium V3 PRO model as `/api/predict/{filename}`.
 * Keep this type only for older branches or saved UI experiments that still
 * expect an explicit channel descriptor.
 */
export interface DualChannelPredictionResult extends PredictionResult {
    /** `true` when a historical dual-input model was used. */
    dual_channel: boolean;
    /** Fixed ordered tuple describing the channel stack. */
    channels: ['hmi_magnetogram', 'aia_193'];
}

// ---------------------------------------------------------------------------
// Agent Lab (read-only scientific audit layer)
// ---------------------------------------------------------------------------
//
// These mirror the Pydantic models in `auralis-back/src/agents/schemas.py`.
// The agents are a read-only audit/decision-support layer: they summarise
// existing artifacts and recommend data priorities. Nothing here measures or
// implies real-world model improvement.

/** Activity bin in raw SI space (percentage points for errors) (thresholds 1.41 / 1.75). */
export type ActivityBin = 'low' | 'medium' | 'high';

/** Advisory severity for an audit finding. */
export type Severity = 'info' | 'notice' | 'warning';

/** A single observation produced by an agent. */
export interface AgentFinding {
    key: string;
    label: string;
    detail: string;
    severity: Severity;
    /** Optional supporting metrics; keys vary per finding. */
    evidence: Record<string, number>;
}

/** An explicit caveat bounding how far a finding can be trusted. */
export interface AgentLimitation {
    key: string;
    detail: string;
}

/** Common envelope shared by every agent report. */
export interface AgentReportBase {
    agent_name: string;
    summary: string;
    /** Heuristic audit confidence in [0, 1] — NOT prediction accuracy. */
    confidence: number;
    findings: AgentFinding[];
    limitations: AgentLimitation[];
    /** ISO-8601 UTC timestamp. */
    generated_at: string;
}

/** Count + share for one activity bin. */
export interface BinStat {
    count: number;
    /** Fraction of the parent population in [0, 1]. */
    share: number;
}

/** Typed temporal-coverage summary. */
export interface DateCoverage {
    first_date: string | null;
    last_date: string | null;
    year_min: number | null;
    year_max: number | null;
    distinct_years: number;
}

/** Typed distribution indicators from metadata columns only. */
export interface OutlierIndicators {
    sunspot_index_min: number;
    sunspot_index_max: number;
    abs_mean_value_max: number | null;
    samples_high_abs_mean: number;
}

/** Data Quality Agent report. */
export interface DataQualityReport extends AgentReportBase {
    full_distribution: Record<ActivityBin, BinStat>;
    train_distribution: Record<ActivityBin, BinStat>;
    val_distribution: Record<ActivityBin, BinStat>;
    low_activity_underrepresented: boolean;
    minority_bin: ActivityBin;
    date_coverage: DateCoverage;
    outlier_indicators: OutlierIndicators | null;
}

/** One hold-out sample, used for the top-error tables. */
export interface ErrorSample {
    filename: string;
    date: string | null;
    real: number;
    predicted: number;
    error: number;
    residual: number;
    activity_bin: ActivityBin;
}

/** Error Analysis Agent report. */
export interface ErrorAnalysisReport extends AgentReportBase {
    mae_by_bin: Record<ActivityBin, number>;
    rmse_by_bin: Record<ActivityBin, number>;
    residual_mean_by_bin: Record<ActivityBin, number>;
    top_errors: ErrorSample[];
    tail_extreme_count: number;
    tail_extreme_mae: number | null;
    /** True when MAE differs little across bins. */
    error_is_flat: boolean;
    mae_spread: number;
}

/** XAI Review Agent report (Phase 1 — inventory + strategy, no sweep). */
export interface XAIReviewReport extends AgentReportBase {
    faithfulness_endpoint_available: boolean;
    available_assets: string[];
    sampled_strategy_recommendation: string;
    /** e.g. "deferred". */
    sweep_status: string;
}

/** One candidate active-learning action and its decision-support utility. */
export interface BanditActionUtility {
    action_id: string;
    action_name: string;
    description: string;
    /** Heuristic utility from current audit signals — NOT measured gain. */
    utility: number;
}

/** One epsilon-greedy bandit round. */
export interface BanditRound {
    round_index: number;
    selected_action: string;
    is_exploration: boolean;
    reward: number;
    /** Heuristic regret vs the best utility, not real-world model gain. */
    regret: number;
}

/** Active Learning Agent report (deterministic contextual bandit). */
export interface ActiveLearningReport extends AgentReportBase {
    state_vector: Record<string, number>;
    action_utilities: BanditActionUtility[];
    rounds: BanditRound[];
    action_distribution: Record<string, number>;
    best_recommendation: BanditActionUtility;
    cumulative_regret: number[];
    epsilon: number;
    seed: number;
    n_rounds: number;
}

/** Coordinator audit brief combining all four agents. */
export interface FullAgentReport extends AgentReportBase {
    dataset_health_summary: string;
    model_weakness_summary: string;
    xai_caution_summary: string;
    active_learning_recommendation: string;
    recommended_next_steps: string[];
    data_quality: DataQualityReport;
    error_analysis: ErrorAnalysisReport;
    xai_review: XAIReviewReport;
    active_learning: ActiveLearningReport;
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
