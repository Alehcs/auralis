// Count completed Needle render callbacks, including XR; never call this GPU time.
export function summarizeFrames(times, durationMs) {
  const intervals = times.slice(1).map((t, i) => t - times[i]).sort((a, b) => a - b);
  const percentile = p => intervals.length ? intervals[Math.min(intervals.length - 1, Math.ceil(intervals.length * p) - 1)] : null;
  return { frames: times.length, durationMs, renderHz: durationMs > 0 ? times.length * 1000 / durationMs : 0,
    medianIntervalMs: percentile(.5), p95IntervalMs: percentile(.95),
    intervalsOver50ms: intervals.filter(t => t > 50).length,
    method: 'Needle post_render_callbacks wall-clock cadence; not GPU time or physical tracking quality' };
}
