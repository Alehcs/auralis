import { useEffect, useState } from 'react';
import { getStats } from './api';
import type { SystemStats } from './types';

export const metricProtocol = (stats: SystemStats | null) =>
  stats ? (stats.evaluation_protocol.startsWith('MC Dropout') ? 'MC T=20' : 'ONNX eval') : '—';

/** Labels follow the responding instance; unavailable metadata stays unavailable. */
export function useModelStats() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  useEffect(() => {
    let active = true;
    getStats().then(value => { if (active) setStats(value); }).catch(() => {});
    return () => { active = false; };
  }, []);
  return stats;
}
