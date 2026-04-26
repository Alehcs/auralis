import { useState, useEffect } from 'react';
import { Activity, BarChart2 } from 'lucide-react';
import { getStats } from '@/lib/api';
import type { SystemStats } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

export function GlobalMetrics() {
  const { t } = useLanguage();
  const e = t.experiments;

  const [stats,   setStats]   = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats().then(setStats).finally(() => setLoading(false));
  }, []);

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
      value:     loading ? '—' : (stats?.r2_score.toFixed(3) ?? '—'),
      sub:       e.r2Desc,
      Icon:      BarChart2,
      iconBg:    'bg-green-500/20',
      iconColor: 'text-green-400',
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
