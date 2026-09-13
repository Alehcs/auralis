import test from 'node:test';
import assert from 'node:assert/strict';
import { summarizeFrames } from '../src/render-sample.mjs';
test('counts cadence over the complete window, including startup stalls', () => {
  const result = summarizeFrames([500, 520, 540, 640], 1000);
  assert.equal(result.renderHz, 4);
  assert.equal(result.medianIntervalMs, 20);
  assert.equal(result.p95IntervalMs, 100);
  assert.equal(result.intervalsOver50ms, 1);
});
test('no rendered frames is zero throughput, not a passing sample', () => {
  assert.equal(summarizeFrames([], 30000).renderHz, 0);
  assert.equal(summarizeFrames([], 30000).p95IntervalMs, null);
});
