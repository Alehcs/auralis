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
import { getBenchmark } from '@/lib/api';
import type { BenchmarkResult } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

// ---------------------------------------------------------------------------
// Shared hook
// ---------------------------------------------------------------------------

function useBenchmark() {
  const [data, setData] = useState<BenchmarkResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBenchmark()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

interface TItem { name: string; value: number; color: string }
interface TProps { active?: boolean; payload?: TItem[]; label?: string }

function ChartTooltip({ active, payload, label }: TProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
      <p className="text-neutral-400 mb-1.5">{label}</p>
      {payload.map((e) => (
        <div key={e.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: e.color }} />
          <span className="text-neutral-300">{e.name}:</span>
          <span className="text-white font-semibold">{e.value.toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Model comparison — horizontal bar chart (right column)
// ---------------------------------------------------------------------------

export function ModelComparisonChart() {
  const { data, loading, error } = useBenchmark();
  const { t } = useLanguage();
  const e = t.experiments;

  // Normalise params to [0, 1] so all three bars share the same X axis
  const allModels = data
    ? [
      ...(data.vgg11 ? [data.vgg11] : []),
      data.baseline,
      data.proposed,
    ]
    : [];

  const maxParams = Math.max(...allModels.map((m) => m.parameters), 1);

  const rows = allModels.map((m) => ({
    model: m.name,
    mae: m.mae,
    rmse: m.rmse,
    params_norm: parseFloat((m.parameters / maxParams).toFixed(4)),
    params_label: m.parameters >= 1_000_000
      ? `${(m.parameters / 1_000_000).toFixed(1)}M`
      : `${(m.parameters / 1_000).toFixed(0)}K`,
  }));

  // Custom tooltip that shows params_norm as the real param count
  const paramLabels = Object.fromEntries(rows.map((r) => [r.model, r.params_label]));

  function TooltipWithParams({ active, payload, label }: {
    active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string;
  }) {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
        <p className="text-neutral-400 mb-1.5">{label}</p>
        {payload.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: item.color }} />
            <span className="text-neutral-300">{item.name}:</span>
            <span className="text-white font-semibold">
              {item.name === 'params'
                ? paramLabels[label ?? ''] ?? item.value.toFixed(2)
                : item.value.toFixed(4)}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-neutral-800">
        <div className="text-[15px] font-semibold text-white">{e.modelComparison}</div>
        <div className="text-[11px] text-neutral-500 mt-0.5">{e.lowerBetter}</div>
      </div>

      <div className="p-5">
        {loading && (
          <div className="flex items-center justify-center h-60 text-neutral-600 text-sm">{e.loading}</div>
        )}
        {error && (
          <div className="text-xs text-red-400 font-mono">{error}</div>
        )}
        {!loading && !error && data && (
          <>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={rows}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                  barCategoryGap="22%"
                  barGap={2}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" horizontal={false} />
                  <XAxis
                    type="number"
                    domain={[0, 'auto']}
                    tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={{ stroke: '#404040' }}
                    tickLine={false}
                    tickFormatter={(v: number) => v.toFixed(2)}
                  />
                  <YAxis
                    type="category"
                    dataKey="model"
                    tick={{ fill: '#a3a3a3', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={false}
                    tickLine={false}
                    width={90}
                  />
                  <Tooltip content={<TooltipWithParams />} cursor={{ fill: '#ffffff08' }} />
                  <Bar dataKey="mae" name="mae" fill="#f59e0b" radius={[0, 2, 2, 0]} maxBarSize={12} />
                  <Bar dataKey="rmse" name="rmse" fill="#38bdf8" radius={[0, 2, 2, 0]} maxBarSize={12} />
                  <Bar dataKey="params_norm" name="params" fill="#a78bfa" radius={[0, 2, 2, 0]} maxBarSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 mt-1 px-1">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-400 inline-block" />
                <span className="text-[10px] text-neutral-500 font-mono">mae</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-sky-400 inline-block" />
                <span className="text-[10px] text-neutral-500 font-mono">rmse</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-violet-400 inline-block" />
                <span className="text-[10px] text-neutral-500 font-mono">params</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Model comparison — table (left column row 3)
// ---------------------------------------------------------------------------

export function ModelComparisonTable() {
  const { data, loading, error } = useBenchmark();
  const { t } = useLanguage();
  const e = t.experiments;

  const rows = data
    ? [
      { m: data.proposed, highlight: true },
      ...(data.vgg11 ? [{ m: data.vgg11, highlight: false }] : []),
      { m: data.baseline, highlight: false },
    ]
    : [];

  const count = rows.length;

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-neutral-800 flex items-start justify-between">
        <div>
          <div className="text-[15px] font-semibold text-white">{e.modelTable}</div>
        </div>
        <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
          {count} {e.candidates}
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center p-10 text-neutral-600 text-sm">{e.loading}</div>
      )}
      {error && (
        <div className="px-5 py-4 text-xs text-red-400 font-mono">{error}</div>
      )}
      {!loading && !error && data && (
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="text-left px-5 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colModel}</th>
              <th className="text-right px-4 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colMae}</th>
              <th className="text-right px-4 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colRmse}</th>
              <th className="text-right px-4 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colR2}</th>
              <th className="text-right px-5 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colParams}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ m, highlight }, idx) => (
              <tr
                key={m.name}
                className={`border-b border-neutral-800/50 ${idx % 2 === 0 ? '' : 'bg-neutral-800/20'}`}
              >
                <td className={`px-5 py-3 ${highlight ? 'text-white font-semibold' : 'text-neutral-400'}`}>
                  {m.name}
                </td>
                <td className={`px-4 py-3 text-right ${highlight ? 'text-white' : 'text-neutral-400'}`}>
                  {m.mae.toFixed(4)}
                </td>
                <td className={`px-4 py-3 text-right ${highlight ? 'text-white' : 'text-neutral-400'}`}>
                  {m.rmse.toFixed(4)}
                </td>
                <td className={`px-4 py-3 text-right ${highlight ? 'text-white' : 'text-neutral-400'}`}>
                  {m.r2_score.toFixed(3)}
                </td>
                <td className="px-5 py-3 text-right text-neutral-400">
                  {m.parameters >= 1_000_000
                    ? `${(m.parameters / 1_000_000).toFixed(0)}M`
                    : m.parameters >= 1_000
                      ? `${(m.parameters / 1_000).toFixed(0)}K`
                      : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Legacy default export (kept for backward compat)
// ---------------------------------------------------------------------------

export function ArchitectureComparison() {
  return (
    <div className="space-y-4">
      <ModelComparisonChart />
      <ModelComparisonTable />
    </div>
  );
}
