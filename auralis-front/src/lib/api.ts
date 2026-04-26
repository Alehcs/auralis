/**
 * API Client for Auralis Backend.
 *
 * Base URL defaults to http://localhost:8000 (configurable via VITE_API_URL).
 */

import type {
    ImageListResponse,
    PredictionResult,
    SystemStats,
    LogEntry,
    HealthResponse,
    BenchmarkResult,
    XAIFaithfulnessResult,
    ExperimentEntry,
} from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Generic fetcher
// ---------------------------------------------------------------------------

async function fetchJson<T>(path: string): Promise<T> {
    const res = await fetch(`${API_URL}${path}`);
    if (!res.ok) {
        const detail = await res.text().catch(() => res.statusText);
        throw new Error(`API ${res.status}: ${detail}`);
    }
    return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

/** Health check. */
export function healthCheck(): Promise<HealthResponse> {
    return fetchJson<HealthResponse>('/health');
}

/** List all processed .npy images, sorted by date descending. */
export function getImageList(): Promise<ImageListResponse> {
    return fetchJson<ImageListResponse>('/api/images/list');
}

/**
 * Build the full URL for rendering a .npy magnetogram as PNG.
 * Use this as the `src` attribute for an `<img>` tag.
 */
export function getImageUrl(filename: string): string {
    return `${API_URL}/api/images/${encodeURIComponent(filename)}`;
}

/** Run Coronium prediction on a processed image. */
export function predict(filename: string): Promise<PredictionResult> {
    return fetchJson<PredictionResult>(
        `/api/predict/${encodeURIComponent(filename)}`,
    );
}

/** Fetch dataset statistics (image count, disk usage, MAE). */
export function getStats(): Promise<SystemStats> {
    return fetchJson<SystemStats>('/api/stats');
}

/** Fetch the last 50 lines from each .log file. */
export function getLogs(): Promise<LogEntry[]> {
    return fetchJson<LogEntry[]>('/api/logs');
}

/** Fetch architecture benchmark: ResNet18 (baseline) vs Coronium. */
export function getBenchmark(): Promise<BenchmarkResult> {
    return fetchJson<BenchmarkResult>('/api/benchmark');
}

/** Compute/fetch XAI faithfulness curve for a magnetogram. */
export function getXAIFaithfulness(filename?: string): Promise<XAIFaithfulnessResult> {
    const qs = filename ? `?filename=${encodeURIComponent(filename)}` : '';
    return fetchJson<XAIFaithfulnessResult>(`/api/xai/faithfulness${qs}`);
}

/** List all experiment runs (sorted by date descending). */
export function getExperiments(): Promise<ExperimentEntry[]> {
    return fetchJson<ExperimentEntry[]>('/api/experiments');
}

/**
 * Build the full URL for rendering an AIA 193Å EUV image.
 * The backend derives EUV from real AIA data (data/aia/) when available,
 * or synthesizes it from the co-registered magnetogram as a proxy.
 */
export function getAiaUrl(filename: string): string {
    return `${API_URL}/api/aia/${encodeURIComponent(filename)}`;
}

/**
 * Run CoroniumDual prediction on [Magnetogram, AIA 193Å].
 * Falls back to single-channel inference when dual weights are not yet trained.
 */
export function predictDual(filename: string): Promise<PredictionResult> {
    return fetchJson<PredictionResult>(
        `/api/predict-dual/${encodeURIComponent(filename)}`,
    );
}

/** Fetch raw JSON metadata for a single experiment run. */
export function getExperimentMetadata(filename: string): Promise<unknown> {
    return fetchJson<unknown>(`/api/experiments/${encodeURIComponent(filename)}`);
}

/** Fetch predicted-vs-actual comparison data (352 validation samples). */
export function getResultsComparison(): Promise<{ real: number; predicted: number; error: number }[]> {
    return fetchJson<{ real: number; predicted: number; error: number }[]>('/api/results-comparison');
}

/**
 * Build the full URL for the 3-panel Grad-CAM figure (B+ | B− | Grad-CAM on |B|).
 * Use this as the `src` attribute for an `<img>` tag.
 */
export function getExplainPanelsUrl(filename: string): string {
    return `${API_URL}/api/explain-panels/${encodeURIComponent(filename)}`;
}

export interface GradCAMLayer {
    layer: string;
    activation_pct: number;
    image: string; // base64 PNG
}

/** Fetch Grad-CAM heatmaps for stage2, stage3, and stage4. */
export function getExplainLayers(filename: string): Promise<GradCAMLayer[]> {
    return fetchJson<GradCAMLayer[]>(`/api/explain-layers/${encodeURIComponent(filename)}`);
}

export interface PolarityPoint {
    date: string;
    b_pos: number;
    b_neg: number;
}

/** Fetch B+ / B− mean flux time-series for the most recent images. */
export function getPolaritySeries(limit = 48): Promise<PolarityPoint[]> {
    return fetchJson<PolarityPoint[]>(`/api/polarity-series?limit=${limit}`);
}
