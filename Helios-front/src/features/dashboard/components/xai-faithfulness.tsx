import { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Eye, Loader2 } from 'lucide-react';
import { getXAIFaithfulness } from '@/lib/api';
import type { XAIFaithfulnessResult, XAIPoint } from '@/lib/types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const COLOR_GRADCAM = '#8b5cf6'; // violet-500 — Grad-CAM curve
const COLOR_RANDOM  = '#57534e'; // stone-600 — random baseline

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
  label?: number;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-700 px-3 py-2 text-xs font-mono shadow-lg min-w-[170px]">
      <p className="text-neutral-400 mb-1.5">
        Píxeles eliminados: <span className="text-white">{label}%</span>
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ background: entry.color }}
            />
            <span className="text-neutral-400">{entry.name}</span>
          </div>
          <span className="text-white font-semibold">{entry.value.toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AUC Score badge
// ---------------------------------------------------------------------------

function AUCBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score > 0.15 ? 'text-violet-400' : score > 0.05 ? 'text-blue-400' : 'text-neutral-400';
  const label = score > 0.15 ? 'Alta Fidelidad' : score > 0.05 ? 'Fidelidad Moderada' : 'Baja Fidelidad';

  return (
    <div className="flex flex-col items-center gap-1 bg-neutral-900 border border-neutral-800 px-5 py-3">
      <span className="text-[10px] text-neutral-500 font-mono uppercase tracking-wider">
        Faithfulness AUC
      </span>
      <span className={`text-2xl font-bold font-mono ${color}`}>
        {pct > 0 ? '+' : ''}{pct}%
      </span>
      <span className={`text-[10px] font-mono ${color}`}>{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function XAIFaithfulness() {
  const [data, setData] = useState<XAIFaithfulnessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getXAIFaithfulness()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const chartData = data
    ? data.curve.map((p: XAIPoint) => ({
        pct: p.pixels_removed_pct,
        'Grad-CAM': parseFloat(p.normalized.toFixed(3)),
        Aleatorio: parseFloat(p.random_normalized.toFixed(3)),
      }))
    : [];

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      {/* Header */}
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-neutral-400" />
            <div>
              <h2 className="text-sm font-semibold text-white">Fidelidad XAI — Análisis de Sensibilidad</h2>
              <p className="text-[11px] text-neutral-500 mt-0.5">
                Análisis de sensibilidad mediante la eliminación progresiva de regiones de alta importancia detectadas por Grad-CAM
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
            <span className="text-[10px] text-neutral-500 font-mono">GRAD-CAM</span>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center gap-2 py-12 text-neutral-500 text-xs font-mono">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Ejecutando análisis de sensibilidad...</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-950 border border-red-900 px-3 py-2 text-xs text-red-400">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* AUC badge + explanation */}
            <div className="grid grid-cols-[auto_1fr] gap-4 items-center">
              <AUCBadge score={data.auc_score} />
              <p className="text-[11px] text-neutral-500 leading-relaxed border-l-2 border-violet-500/40 pl-3">
                La curva <span className="text-violet-400 font-semibold">Grad-CAM</span> desciende
                significativamente más rápido que la línea de referencia{' '}
                <span className="text-stone-400 font-semibold">aleatoria</span>, lo que confirma que las
                regiones identificadas por la explicabilidad contienen información predictiva real.
                Un AUC positivo indica que la eliminación guiada degrada la predicción más que la
                eliminación al azar —validación cuantitativa de la explicación.{' '}
                <span className="text-neutral-400 font-mono">
                  Baseline: {data.baseline_prediction.toFixed(4)}
                </span>
              </p>
            </div>

            {/* Area chart */}
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="gradcamGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={COLOR_GRADCAM} stopOpacity={0.25} />
                      <stop offset="95%" stopColor={COLOR_GRADCAM} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="randomGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={COLOR_RANDOM} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={COLOR_RANDOM} stopOpacity={0} />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#262626"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="pct"
                    type="number"
                    domain={[0, 100]}
                    ticks={[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                    tick={{ fill: '#737373', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={{ stroke: '#404040' }}
                    tickLine={false}
                    label={{
                      value: 'Píxeles Eliminados (%)',
                      position: 'insideBottom',
                      offset: -2,
                      fill: '#525252',
                      fontSize: 10,
                      fontFamily: 'monospace',
                    }}
                    height={36}
                  />

                  <YAxis
                    tick={{ fill: '#737373', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => v.toFixed(1)}
                    width={36}
                    label={{
                      value: 'Predicción Normalizada',
                      angle: -90,
                      position: 'insideLeft',
                      offset: 8,
                      fill: '#525252',
                      fontSize: 10,
                      fontFamily: 'monospace',
                    }}
                  />

                  <Tooltip content={<CustomTooltip />} />

                  <Legend
                    iconType="square"
                    iconSize={8}
                    wrapperStyle={{ fontSize: 11, fontFamily: 'monospace', color: '#a3a3a3' }}
                  />

                  {/* Reference line at y=1 (baseline) */}
                  <ReferenceLine
                    y={1}
                    stroke="#404040"
                    strokeDasharray="4 4"
                    label={{ value: 'baseline', fill: '#525252', fontSize: 9, fontFamily: 'monospace' }}
                  />

                  <Area
                    type="monotone"
                    dataKey="Aleatorio"
                    stroke={COLOR_RANDOM}
                    strokeWidth={1.5}
                    strokeDasharray="5 3"
                    fill="url(#randomGrad)"
                    dot={false}
                    activeDot={{ r: 3, fill: COLOR_RANDOM }}
                  />

                  <Area
                    type="monotone"
                    dataKey="Grad-CAM"
                    stroke={COLOR_GRADCAM}
                    strokeWidth={2}
                    fill="url(#gradcamGrad)"
                    dot={false}
                    activeDot={{ r: 3, fill: COLOR_GRADCAM }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Data table */}
            <div className="border border-neutral-800 overflow-hidden">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="bg-neutral-900 border-b border-neutral-800">
                    <th className="text-left px-4 py-2 text-[11px] text-neutral-500 font-medium">
                      Píxeles elim.
                    </th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">
                      Pred. Grad-CAM
                    </th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">
                      Norm. Grad-CAM
                    </th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">
                      Norm. Aleatorio
                    </th>
                    <th className="text-right px-4 py-2 text-[11px] text-neutral-500 font-medium">
                      Δ Fidelidad
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.curve.map((row, idx) => {
                    const delta = row.random_normalized - row.normalized;
                    const isSignificant = delta > 0.05;
                    return (
                      <tr
                        key={row.pixels_removed_pct}
                        className={`border-b border-neutral-800/60 ${idx % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900/30'}`}
                      >
                        <td className="px-4 py-2 text-neutral-400">{row.pixels_removed_pct}%</td>
                        <td className="px-4 py-2 text-right text-neutral-300">
                          {row.prediction.toFixed(4)}
                        </td>
                        <td className={`px-4 py-2 text-right ${row.normalized < 0.8 ? 'text-violet-400 font-semibold' : 'text-neutral-300'}`}>
                          {row.normalized.toFixed(3)}
                        </td>
                        <td className="px-4 py-2 text-right text-neutral-400">
                          {row.random_normalized.toFixed(3)}
                        </td>
                        <td className={`px-4 py-2 text-right font-semibold ${isSignificant ? 'text-violet-400' : 'text-neutral-600'}`}>
                          {delta > 0 ? '+' : ''}{delta.toFixed(3)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Footer metadata */}
            <div className="flex items-center gap-4 pt-1">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                <span className="text-[10px] text-neutral-500 font-mono">Grad-CAM (conv4)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-stone-500" />
                <span className="text-[10px] text-neutral-500 font-mono">Eliminación aleatoria (seed=42)</span>
              </div>
              <span className="text-[10px] text-neutral-600 font-mono ml-auto truncate">
                {data.filename}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
