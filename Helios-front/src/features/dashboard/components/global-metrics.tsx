import { useState, useEffect } from 'react';
import { TrendingDown, Activity, Award, Loader2 } from 'lucide-react';
import { getStats } from '@/lib/api';
import type { SystemStats } from '@/lib/types';

interface MetricCardProps {
  icon: React.ElementType;
  label: string;
  sublabel: string;
  value: string;
  unit?: string;
  target: string;
  iconColor: string;
  dotColor: string;
}

function MetricCard({ icon: Icon, label, sublabel, value, unit, target, iconColor, dotColor }: MetricCardProps) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div className={`w-8 h-8 bg-neutral-800 border border-neutral-700 flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
          <span className="text-[10px] font-mono text-neutral-500">LIVE</span>
        </div>
      </div>

      <div>
        <p className="text-[11px] text-neutral-500 mb-1">{label}</p>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-mono text-white">{value}</span>
          {unit && <span className="text-xs font-mono text-neutral-500">{unit}</span>}
        </div>
        <p className="text-[10px] text-neutral-600 font-mono mt-1">{sublabel}</p>
      </div>

      <div className="pt-2 border-t border-neutral-800">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-neutral-600 font-mono">target</span>
          <span className="text-[10px] text-neutral-400 font-mono">{target}</span>
        </div>
      </div>
    </div>
  );
}

export function GlobalMetrics() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-neutral-950 border border-neutral-800">
        <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
          <h2 className="text-sm font-semibold text-white">Métricas Globales del Modelo</h2>
          <p className="text-[11px] text-neutral-500 mt-0.5">SolarNet V2 PRO · Conjunto de validación</p>
        </div>
        <div className="p-8 flex items-center justify-center">
          <Loader2 className="w-5 h-5 text-neutral-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-950 border border-neutral-800">
        <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
          <h2 className="text-sm font-semibold text-white">Métricas Globales del Modelo</h2>
        </div>
        <div className="p-4">
          <div className="bg-red-950 border border-red-900 px-3 py-2 text-xs text-red-400 font-mono">{error}</div>
        </div>
      </div>
    );
  }

  const cards: MetricCardProps[] = [
    {
      icon: TrendingDown,
      label: 'MAE — Error Absoluto Medio',
      sublabel: 'Mean Absolute Error',
      value: stats?.mae.toFixed(4) ?? '--',
      unit: '%',
      target: '< 0.50',
      iconColor: 'text-green-400',
      dotColor: 'bg-green-500',
    },
    {
      icon: Activity,
      label: 'RMSE — Raíz del Error Cuadrático',
      sublabel: 'Root Mean Squared Error',
      value: stats?.rmse.toFixed(4) ?? '--',
      unit: '%',
      target: '< 0.25',
      iconColor: 'text-blue-400',
      dotColor: 'bg-blue-500',
    },
    {
      icon: Award,
      label: 'R² Score — Coeficiente de Determinación',
      sublabel: 'Coefficient of Determination',
      value: stats?.r2_score.toFixed(4) ?? '--',
      target: '> 0.85',
      iconColor: 'text-violet-400',
      dotColor: 'bg-violet-500',
    },
  ];

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <h2 className="text-sm font-semibold text-white">Métricas Globales del Modelo</h2>
        <p className="text-[11px] text-neutral-500 mt-0.5">SolarNet V2 PRO · Conjunto de validación</p>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {cards.map((card) => (
            <MetricCard key={card.label} {...card} />
          ))}
        </div>
      </div>
    </div>
  );
}
