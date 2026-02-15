/**
 * API Client for HeliosPipeline Backend.
 *
 * Base URL defaults to http://localhost:8000 (configurable via VITE_API_URL).
 */

import type {
    ImageListResponse,
    PredictionResult,
    SystemStats,
    LogEntry,
    HealthResponse,
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

/** Run SolarNet prediction on a processed image. */
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
