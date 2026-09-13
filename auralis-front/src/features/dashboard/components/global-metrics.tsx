import { useState, useEffect } from 'react';
import { Activity, BarChart2 } from 'lucide-react';
import { getStats } from '@/lib/api';
import type { SystemStats } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

/** Colour for R² — green ≥ 0.5, amber ≥ 0, red < 0 (distribution shift). */
function r2Color(val: number | null): string {
  if (val === null) return 'bg-neutral-500/20';
  if (val >= 0.5)  return 'bg-green-500/20';
  if (val >= 0)    return 'bg-amber-500/20';
  return                  'bg-red-500/20';
}
function r2IconColor(val: number | null): string {
  if (val === null) return 'text-neutral-400';
  if (val >= 0.5)  return 'text-green-400';
  if (val >= 0)    return 'text-amber-400';
  return                  'text-red-400';
}

export function GlobalMetrics() {
  const { t } = useLanguage();
  const e = t.experiments;

  const [stats,   setStats]   = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats().then(setStats).catch(() => setStats(null)).finally(() => setLoading(false));
  }, []);

  const r2Val = stats?.r2_score ?? null;

  const CARDS = [
    {
      label:     'V3.1 MC MAE',
      value:     loading ? '—' : (stats?.mae.toFixed(4) ?? '—'),
      sub:       `${e.maeDesc} · SI pp`,
      Icon:      null, // Σ symbol
      iconBg:    'bg-orange-500/20',
      iconColor: 'text-orange-400',
    },
    {
      label:     'V3.1 MC RMSE',
      value:     loading ? '—' : (stats?.rmse.toFixed(4) ?? '—'),
      sub:       `${e.rmseDesc} · SI pp`,
      Icon:      Activity,
      iconBg:    'bg-teal-500/20',
      iconColor: 'text-teal-400',
    },
    {
      label:     'V3.1 MC R²',
      value:     loading ? '—' : (r2Val !== null ? r2Val.toFixed(3) : '—'),
      sub:       e.r2Desc,
      Icon:      BarChart2,
      iconBg:    r2Color(loading ? null : r2Val),
      iconColor: r2IconColor(loading ? null : r2Val),
    },
    {
      label: 'V3.1 MC MAPE',
      value: loading ? '—' : (stats ? `${stats.mape.toFixed(2)}%` : '—'),
      sub: 'Nonzero targets · relative error',
      Icon: BarChart2,
      iconBg: 'bg-sky-500/20',
      iconColor: 'text-sky-400',
    },
  ] as const;

  return (
    <div className="space-y-4">
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {CARDS.map((card) => (
        <div
          key={card.label}
          className="bg-neutral-900 border border-neutral-800 rounded-xl p-5"
        >
          <div className="flex items-start justify-between">
            <div className="text-[11px] text-neutral-500 tracking-[0.14em] font-mono font-medium">
              {card.label}
            </div>
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${card.iconBg}`}>
              {card.Icon
                ? <card.Icon className={`w-4 h-4 ${card.iconColor}`} />
                : <span className={`text-[16px] font-bold leading-none ${card.iconColor}`}>Σ</span>
              }
            </div>
          </div>
          <div className="text-[38px] font-mono font-bold text-white mt-3 leading-none tracking-tight">
            {card.value}
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">{card.sub}</div>
        </div>
      ))}
    </div>
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 overflow-x-auto">
      <p className="text-sm text-white mb-2">Coronium V3.1 · protocols on the same 263 observations</p>
      <p className="text-[11px] text-neutral-500 mb-3">Selection validation · overlap 0 · no independent or temporal test. MC: T=20, MPS, batch 32, seed 42. ONNX: deterministic CPU, batch 1.</p>
      <table className="w-full text-xs text-neutral-300 font-mono">
        <thead><tr className="text-neutral-500 text-right"><th className="text-left py-2">Protocol</th><th>MAE (SI pp)</th><th>RMSE (SI pp)</th><th>R²</th><th>MAPE (%)</th></tr></thead>
        <tbody>
          <tr className="text-right"><td className="text-left py-2">MC Dropout T=20</td><td>{stats?.mae.toFixed(4) ?? '—'}</td><td>{stats?.rmse.toFixed(4) ?? '—'}</td><td>{stats?.r2_score.toFixed(4) ?? '—'}</td><td>{stats?.mape.toFixed(2) ?? '—'}</td></tr>
          <tr className="text-right"><td className="text-left py-2">Deterministic ONNX</td>{['mae', 'rmse', 'r2', 'mape'].map((key) => <td key={key}>{stats?.serving_deterministic.onnx[key]?.toFixed(key === 'mape' ? 2 : 4) ?? '—'}</td>)}</tr>
        </tbody>
      </table>
    </div>
    </div>
  );
}
