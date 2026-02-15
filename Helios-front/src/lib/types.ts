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
}

// -- Stats -----------------------------------------------------------------

export interface SystemStats {
    total_images: number;
    disk_usage_mb: number;
    mae: number;
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

// -- Errors ----------------------------------------------------------------

export interface ApiError {
    error: string;
    message: string;
    status: number;
}
