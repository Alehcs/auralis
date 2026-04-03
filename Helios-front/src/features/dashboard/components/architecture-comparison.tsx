import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Layers, TrendingDown } from 'lucide-react';
import { getBenchmark } from '@/lib/api';
import type { BenchmarkResult } from '@/lib/types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const COLOR_BASELINE = '#78716c';  // stone-500 — sober neutral for ResNet18
const COLOR_PROPOSED = '#3b82f6';  // blue-500 — clear but non-aggressive for SolarNet

// ---------------------------------------------------------------------------
// Custom Tooltip
// ---------------------------------------------------------------------------

interface TooltipPayloadItem {
  name: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-700 px-3 py-2 text-xs font-mono shadow-lg">
      <p className="text-neutral-400 mb-1.5">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ background: entry.color }}
          />
          <span className="text-neutral-300">{entry.name}:</span>
          <span className="text-white font-semibold">{entry.value.toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reduction badge
// ---------------------------------------------------------------------------

function ReductionBadge({ label, pct }: { label: string; pct: number }) {
  return (
    <div className="flex flex-col items-center gap-1 bg-neutral-900 border border-neutral-800 px-4 py-3">
      <div className="flex items-center gap-1.5">
        <TrendingDown className="w-3.5 h-3.5 text-blue-400" />
        <span className="text-[10px] text-neutral-500 font-mono uppercase tracking-wider">{label}</span>
      </div>
      <span className="text-2xl font-bold text-blue-400 font-mono">−{pct}%</span>
      <span className="text-[10px] text-neutral-600 font-mono">vs ResNet18</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ArchitectureComparison() {
  const [data, setData] = useState<BenchmarkResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBenchmark()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const chartData = data
    ? [
        { metric: 'MAE', ResNet18: data.baseline.mae, SolarNet: data.proposed.mae },
        { metric: 'RMSE', ResNet18: data.baseline.rmse, SolarNet: data.proposed.rmse },
      ]
    : [];

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      {/* Header */}
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-neutral-400" />
            <div>
              <h2 className="text-sm font-semibold text-white">Comparación de Arquitecturas</h2>
              <p className="text-[11px] text-neutral-500 mt-0.5">
                ResNet18 (Baseline) vs. SolarNet V2 PRO · Conjunto de Validación
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            <span className="text-[10px] text-neutral-500 font-mono">BENCHMARK</span>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Loading / error states */}
        {loading && (
          <div className="flex items-center justify-center py-10 text-neutral-500 text-xs font-mono">
            Cargando resultados...
          </div>
        )}

        {error && (
          <div className="bg-red-950 border border-red-900 px-3 py-2 text-xs text-red-400">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* Reduction badges */}
            <div className="grid grid-cols-2 gap-3">
              <ReductionBadge label="Reducción MAE" pct={data.mae_reduction_pct} />
              <ReductionBadge label="Reducción RMSE" pct={data.rmse_reduction_pct} />
            </div>

            {/* Explanatory text */}
            <p className="text-[11px] text-neutral-500 leading-relaxed border-l-2 border-blue-500/40 pl-3">
              SolarNet V2 PRO alcanza una reducción del{' '}
              <span className="text-blue-400 font-semibold">{data.mae_reduction_pct}% en MAE</span> y del{' '}
              <span className="text-blue-400 font-semibold">{data.rmse_reduction_pct}% en RMSE</span> respecto
              al baseline ResNet18, con apenas{' '}
              <span className="text-white font-mono">
                {(data.proposed.parameters / 1000).toFixed(0)}K parámetros
              </span>{' '}
              frente a los{' '}
              <span className="text-neutral-300 font-mono">
                {(data.baseline.parameters / 1_000_000).toFixed(1)}M
              </span>{' '}
              del baseline — 30× más compacto y {Math.round(data.baseline.inference_ms / data.proposed.inference_ms)}× más rápido en inferencia.
            </p>

            {/* Grouped bar chart */}
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
                  barCategoryGap="30%"
                  barGap={4}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#262626"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="metric"
                    tick={{ fill: '#a3a3a3', fontSize: 11, fontFamily: 'monospace' }}
                    axisLine={{ stroke: '#404040' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#737373', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => v.toFixed(2)}
                    domain={[0, 'auto']}
                    width={40}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: '#ffffff08' }} />
                  <Legend
                    iconType="square"
                    iconSize={8}
                    wrapperStyle={{ fontSize: 11, fontFamily: 'monospace', color: '#a3a3a3' }}
                  />
                  <Bar
                    dataKey="ResNet18"
                    name="ResNet18 (Baseline)"
                    fill={COLOR_BASELINE}
                    radius={[2, 2, 0, 0]}
                    maxBarSize={56}
                  />
                  <Bar
                    dataKey="SolarNet"
                    name="SolarNet V2 PRO"
                    fill={COLOR_PROPOSED}
                    radius={[2, 2, 0, 0]}
                    maxBarSize={56}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Summary table */}
            <div className="border border-neutral-800 overflow-hidden">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="bg-neutral-900 border-b border-neutral-800">
                    <th className="text-left px-4 py-2 text-[11px] text-neutral-500 font-medium">Modelo</th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">MAE</th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">RMSE</th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">R²</th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">Params</th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">Infer. ms</th>
                  </tr>
                </thead>
                <tbody>
                  {[data.baseline, data.proposed].map((m, idx) => (
                    <tr
                      key={m.name}
                      className={`border-b border-neutral-800/60 ${idx % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900/30'}`}
                    >
                      <td className="px-4 py-2.5 flex items-center gap-2">
                        <span
                          className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                          style={{ background: idx === 0 ? COLOR_BASELINE : COLOR_PROPOSED }}
                        />
                        <span className={idx === 0 ? 'text-neutral-400' : 'text-white'}>{m.name}</span>
                      </td>
                      <td className={`px-4 py-2.5 text-right ${idx === 0 ? 'text-neutral-400' : 'text-green-400 font-semibold'}`}>
                        {m.mae.toFixed(4)}
                      </td>
                      <td className={`px-4 py-2.5 text-right ${idx === 0 ? 'text-neutral-400' : 'text-green-400 font-semibold'}`}>
                        {m.rmse.toFixed(4)}
                      </td>
                      <td className={`px-4 py-2.5 text-right ${idx === 0 ? 'text-neutral-400' : 'text-blue-400 font-semibold'}`}>
                        {m.r2_score.toFixed(4)}
                      </td>
                      <td className="px-4 py-2.5 text-right text-neutral-400">
                        {idx === 0
                          ? `${(m.parameters / 1_000_000).toFixed(1)}M`
                          : `${(m.parameters / 1000).toFixed(0)}K`}
                      </td>
                      <td className="px-4 py-2.5 text-right text-neutral-400">
                        {m.inference_ms.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
