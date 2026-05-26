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
    getStats().then(setStats).finally(() => setLoading(false));
  }, []);

  const r2Val = stats?.r2_score ?? null;

  const CARDS = [
    {
      label:     'MAE',
      value:     loading ? '—' : (stats?.mae.toFixed(4) ?? '—'),
      sub:       e.maeDesc,
      Icon:      null, // Σ symbol
      iconBg:    'bg-orange-500/20',
      iconColor: 'text-orange-400',
    },
    {
      label:     'RMSE',
      value:     loading ? '—' : (stats?.rmse.toFixed(4) ?? '—'),
      sub:       e.rmseDesc,
      Icon:      Activity,
      iconBg:    'bg-teal-500/20',
      iconColor: 'text-teal-400',
    },
    {
      label:     'R²',
      value:     loading ? '—' : (r2Val !== null ? r2Val.toFixed(3) : '—'),
      sub:       e.r2Desc,
      Icon:      BarChart2,
      iconBg:    r2Color(loading ? null : r2Val),
      iconColor: r2IconColor(loading ? null : r2Val),
    },
  ] as const;

  return (
    <div className="grid grid-cols-3 gap-4">
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
  );
}
