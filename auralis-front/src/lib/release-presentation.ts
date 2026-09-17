import releases from './release-presentation.json';
import type { SystemStats } from './types';

/** Derived from hash-verified manifests; never supply replacement API metrics. */
export function releasePresentation(stats: SystemStats | null) {
  if (!stats || !(stats.model_version in releases)) return null;
  const release = releases[stats.model_version as keyof typeof releases];
  if (stats.model_name !== release.model_name) return null;
  const isMC = stats.evaluation_protocol.startsWith('MC Dropout');
  const expected = isMC ? release.metrics.mc : release.metrics.deterministic;
  if (!expected || (stats.model_version === '3.2' && !stats.evaluation_protocol.includes('mlas.disable_kleidiai=1'))) return null;
  const actual = [stats.mae, stats.rmse, stats.r2_score, stats.mape];
  const source = [expected.mae, expected.rmse, expected.r2, expected.mape];
  if (stats.validation_observations !== 263 || actual.some((v, i) => !Number.isFinite(v) || Math.abs(v - source[i]) > 1e-10)) return null;
  const det = stats.serving_deterministic?.onnx;
  if (!det || ['mae', 'rmse', 'r2', 'mape'].some(key => Math.abs(det[key] - release.metrics.deterministic[key as keyof typeof release.metrics.deterministic]) > 1e-10 || !Number.isFinite(det[key]))) return null;
  return release;
}

export function releaseLabel(stats: SystemStats | null, language = 'en') {
  const r = releasePresentation(stats);
  return r ? `${r.model_name}${stats?.model_version === '3.2' ? ' C1' : ''} · s${r.seed} · ${language === 'es' ? 'época' : 'epoch'} ${r.epoch}` : '—';
}
