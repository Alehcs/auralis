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
// Chart colour palette
// ---------------------------------------------------------------------------

/** stone-500: neutral tone that recedes visually relative to the proposed model. */
const COLOR_BASELINE = '#78716c';
/** amber-400: warm accent that distinguishes VGG-11 without competing with SolarNet. */
const COLOR_VGG     = '#f59e0b';
/** blue-500: primary brand colour reserved for the proposed SolarNet architecture. */
const COLOR_PROPOSED = '#3b82f6';

// ---------------------------------------------------------------------------
// Custom Tooltip
// ---------------------------------------------------------------------------

/** Single series entry provided by Recharts to a custom tooltip renderer. */
interface TooltipPayloadItem {
  name: string;
  value: number;
  color: string;
}

/** Props injected by Recharts into the `content` prop of `<Tooltip />`. */
interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  /** X-axis category label for the hovered bar group (e.g. `"MAE"`). */
  label?: string;
}

/**
 * Recharts tooltip renderer styled to the dashboard dark theme.
 *
 * Renders a floating card with per-series name/value pairs only when
 * the cursor is over an active data point (`active && payload?.length`).
 */
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

/**
 * Compact KPI badge displaying the relative error reduction of SolarNet
 * over the ResNet-18 baseline for a single metric (MAE or RMSE).
 *
 * @param label - Metric label shown in the badge header (e.g. `"Reducción MAE"`).
 * @param pct   - Reduction percentage as a positive integer (e.g. `50`).
 */
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

/**
 * Dashboard panel comparing SolarNet V2 PRO against ResNet-18 and VGG-11
 * baselines on MAE, RMSE, R², parameter count, and inference latency.
 *
 * Fetches benchmark data from `/api/benchmark` on mount and refreshes
 * every 30 seconds. Renders KPI badges, a grouped bar chart, and a
 * summary table. VGG-11 bars and rows are conditionally rendered only
 * when the API response includes `vgg11` data.
 */
export function ArchitectureComparison() {
  const [data, setData] = useState<BenchmarkResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = () =>
      getBenchmark()
        .then(setData)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));

    fetchData();
    // Poll every 30 s to reflect live benchmarking results without a page reload.
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, []);

  const chartData = data
    ? [
        {
          metric: 'MAE',
          ResNet18: data.baseline.mae,
          ...(data.vgg11 ? { 'VGG-11': data.vgg11.mae } : {}),
          SolarNet: data.proposed.mae,
        },
        {
          metric: 'RMSE',
          ResNet18: data.baseline.rmse,
          ...(data.vgg11 ? { 'VGG-11': data.vgg11.rmse } : {}),
          SolarNet: data.proposed.rmse,
        },
      ]
    : [];

  return (
    <div className="bg-neutral-950 border border-neutral-800">
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
            <div className="grid grid-cols-2 gap-3">
              <ReductionBadge label="Reducción MAE" pct={data.mae_reduction_pct} />
              <ReductionBadge label="Reducción RMSE" pct={data.rmse_reduction_pct} />
            </div>

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
                  {data?.vgg11 && (
                    <Bar
                      dataKey="VGG-11"
                      name="VGG-11 (Baseline)"
                      fill={COLOR_VGG}
                      radius={[2, 2, 0, 0]}
                      maxBarSize={56}
                    />
                  )}
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
                  {([
                    { model: data.baseline, color: COLOR_BASELINE, isProposed: false },
                    ...(data.vgg11 ? [{ model: data.vgg11, color: COLOR_VGG, isProposed: false }] : []),
                    { model: data.proposed, color: COLOR_PROPOSED, isProposed: true },
                  ] as { model: typeof data.baseline; color: string; isProposed: boolean }[]).map(({ model: m, color, isProposed }, idx) => (
                    <tr
                      key={m.name}
                      className={`border-b border-neutral-800/60 ${idx % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900/30'}`}
                    >
                      <td className="px-4 py-2.5 flex items-center gap-2">
                        <span
                          className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                          style={{ background: color }}
                        />
                        <span className={isProposed ? 'text-white' : 'text-neutral-400'}>{m.name}</span>
                      </td>
                      <td className={`px-4 py-2.5 text-right ${isProposed ? 'text-green-400 font-semibold' : 'text-neutral-400'}`}>
                        {m.mae.toFixed(4)}
                      </td>
                      <td className={`px-4 py-2.5 text-right ${isProposed ? 'text-green-400 font-semibold' : 'text-neutral-400'}`}>
                        {m.rmse.toFixed(4)}
                      </td>
                      <td className={`px-4 py-2.5 text-right ${isProposed ? 'text-blue-400 font-semibold' : 'text-neutral-400'}`}>
                        {m.r2_score.toFixed(4)}
                      </td>
                      <td className="px-4 py-2.5 text-right text-neutral-400">
                        {isProposed
                          ? `${(m.parameters / 1000).toFixed(0)}K`
                          : `${(m.parameters / 1_000_000).toFixed(1)}M`}
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
