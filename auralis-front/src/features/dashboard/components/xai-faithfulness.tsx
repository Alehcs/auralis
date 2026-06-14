import { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Eye, Loader2 } from 'lucide-react';
import { getXAIFaithfulness } from '@/lib/api';
import type { XAIFaithfulnessResult, XAIPoint } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

const COLOR_GRADCAM = '#8b5cf6';
const COLOR_RANDOM  = '#57534e';

// Keys used as Recharts dataKey — must stay constant (not translated)
const KEY_GRADCAM = 'Grad-CAM';
const KEY_RANDOM  = 'Random';

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

interface TItem { name: string; value: number; color: string }
interface TProps { active?: boolean; payload?: TItem[]; label?: number; pixelsLabel: string }

function ChartTooltip({ active, payload, label, pixelsLabel }: TProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg min-w-[170px]">
      <p className="text-neutral-400 mb-1.5">{pixelsLabel}: <span className="text-white">{label}%</span></p>
      {payload.map((e) => (
        <div key={e.name} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: e.color }} />
            <span className="text-neutral-400">{e.name}</span>
          </div>
          <span className="text-white font-semibold">{e.value.toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AUC badge
// ---------------------------------------------------------------------------

function AUCBadge({ score, labels }: {
  score: number;
  labels: { aucLabel: string; high: string; moderate: string; low: string };
}) {
  const pct   = Math.round(score * 100);
  const color = score > 0.15 ? 'text-violet-400' : score > 0.05 ? 'text-sky-400' : 'text-neutral-400';
  const label = score > 0.15 ? labels.high : score > 0.05 ? labels.moderate : labels.low;
  return (
    <div className="bg-neutral-800/60 border border-neutral-700/50 rounded-xl px-5 py-4 flex flex-col items-center gap-1 flex-shrink-0">
      <span className="text-[9px] text-neutral-500 font-mono tracking-[0.15em]">{labels.aucLabel}</span>
      <span className={`text-[28px] font-bold font-mono leading-none ${color}`}>
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
  const { t } = useLanguage();
  const e = t.experiments;

  const [data,    setData]    = useState<XAIFaithfulnessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    getXAIFaithfulness()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const chartData = data
    ? data.curve.map((p: XAIPoint) => ({
        pct:          p.pixels_removed_pct,
        [KEY_GRADCAM]: parseFloat(p.normalized.toFixed(3)),
        [KEY_RANDOM]:  parseFloat(p.random_normalized.toFixed(3)),
      }))
    : [];

  const aucLabels = {
    aucLabel: e.aucLabel,
    high:     e.highFidelity,
    moderate: e.moderateFidelity,
    low:      e.lowFidelity,
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-neutral-800 flex items-start justify-between">
        <div>
          <div className="text-[15px] font-semibold text-white">{e.xaiFaithfulness}</div>
          <div className="text-[11px] text-neutral-500 mt-0.5">
            {e.xaiSubtitle}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
          <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
            GRAD-CAM
          </span>
        </div>
      </div>

      <div className="p-5 space-y-5">

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center gap-2 py-14 text-neutral-600 text-xs font-mono">
            <Loader2 className="w-4 h-4 animate-spin" />
            {e.loading}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-950/50 border border-red-900/50 rounded-lg px-3 py-2 text-xs text-red-400 font-mono">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* AUC badge + explanation */}
            <div className="flex items-start gap-4">
              <AUCBadge score={data.auc_score} labels={aucLabels} />
              <p className="text-[12px] text-neutral-400 leading-relaxed border-l-2 border-violet-500/40 pl-4 py-1">
                The <span className="text-violet-400 font-semibold">Grad-CAM</span> curve drops
                significantly faster than the{' '}
                <span className="text-stone-400 font-semibold">random</span> baseline, which
                suggests that the highlighted regions contribute to this prediction. A positive
                AUC means guided removal degrades the output more than random removal in this
                single-image deletion diagnostic; it is a faithfulness indicator, not evidence of
                causal solar-physics reasoning.{' '}
                <span className="text-neutral-500 font-mono text-[11px]">
                  Baseline: {data.baseline_prediction.toFixed(4)}
                </span>
              </p>
            </div>

            {/* Area chart */}
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 20 }}>
                  <defs>
                    <linearGradient id="gradcamGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={COLOR_GRADCAM} stopOpacity={0.25} />
                      <stop offset="95%" stopColor={COLOR_GRADCAM} stopOpacity={0}    />
                    </linearGradient>
                    <linearGradient id="randomGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={COLOR_RANDOM} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={COLOR_RANDOM} stopOpacity={0}    />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                  <XAxis
                    dataKey="pct"
                    type="number"
                    domain={[0, 100]}
                    ticks={[0, 20, 40, 60, 80, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                    tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={{ stroke: '#404040' }}
                    tickLine={false}
                    label={{ value: e.pixelsRemoved, position: 'insideBottom', offset: -12, fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                    height={36}
                  />
                  <YAxis
                    tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => v.toFixed(1)}
                    width={34}
                  />
                  <Tooltip
                    content={(props) => (
                      <ChartTooltip
                        {...props}
                        pixelsLabel={e.pixelsRemoved}
                      />
                    )}
                  />
                  <ReferenceLine y={1} stroke="#404040" strokeDasharray="4 4" />
                  <Area
                    type="monotone"
                    dataKey={KEY_RANDOM}
                    stroke={COLOR_RANDOM}
                    strokeWidth={1.5}
                    strokeDasharray="5 3"
                    fill="url(#randomGrad)"
                    dot={false}
                    activeDot={{ r: 3, fill: COLOR_RANDOM }}
                  />
                  <Area
                    type="monotone"
                    dataKey={KEY_GRADCAM}
                    stroke={COLOR_GRADCAM}
                    strokeWidth={2}
                    fill="url(#gradcamGrad)"
                    dot={false}
                    activeDot={{ r: 3, fill: COLOR_GRADCAM }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-5 px-1">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-violet-500 inline-block" />
                <span className="text-[10px] text-neutral-500 font-mono">{e.gradcam} (conv4 / stage4)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-stone-500 inline-block" />
                <span className="text-[10px] text-neutral-500 font-mono">{e.random} (seed=42)</span>
              </div>
              <span className="text-[10px] text-neutral-600 font-mono ml-auto truncate">{data.filename}</span>
            </div>

            {/* Data table */}
            <div className="border border-neutral-800 rounded-lg overflow-hidden overflow-x-auto">
              <table className="w-full text-xs font-mono min-w-[360px]">
                <thead>
                  <tr className="border-b border-neutral-800 bg-neutral-800/40">
                    <th className="text-left   px-4 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">{e.colPixels}</th>
                    <th className="text-right  px-4 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">{e.colPredGcam}</th>
                    <th className="text-right  px-4 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">{e.colNormGcam}</th>
                    <th className="text-right  px-4 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">{e.colNormRand}</th>
                    <th className="text-right  px-4 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">{e.colDelta}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.curve.map((row, idx) => {
                    const delta = row.random_normalized - row.normalized;
                    return (
                      <tr
                        key={row.pixels_removed_pct}
                        className={`border-b border-neutral-800/40 ${idx % 2 === 0 ? '' : 'bg-neutral-800/20'}`}
                      >
                        <td className="px-4 py-2 text-neutral-500">{row.pixels_removed_pct}%</td>
                        <td className="px-4 py-2 text-right text-neutral-300">{row.prediction.toFixed(4)}</td>
                        <td className={`px-4 py-2 text-right ${row.normalized < 0.8 ? 'text-violet-400 font-semibold' : 'text-neutral-300'}`}>
                          {row.normalized.toFixed(3)}
                        </td>
                        <td className="px-4 py-2 text-right text-neutral-400">{row.random_normalized.toFixed(3)}</td>
                        <td className={`px-4 py-2 text-right font-semibold ${delta > 0.05 ? 'text-violet-400' : 'text-neutral-600'}`}>
                          {delta > 0 ? '+' : ''}{delta.toFixed(3)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
