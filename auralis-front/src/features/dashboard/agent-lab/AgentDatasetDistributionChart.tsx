/**
 * Activity-bin distribution: full corpus vs train vs validation.
 *
 * Plots share (%) per bin so the three splits are comparable despite very
 * different sample counts. The narrative this supports: LOW activity is the
 * minority class, not high activity.
 */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { DataQualityReport, ActivityBin } from '@/lib/types';
import { SPLIT_COLORS } from './AgentCard';

const BINS: ActivityBin[] = ['low', 'medium', 'high'];

interface Row {
  bin: string;
  full: number;
  train: number;
  val: number;
  fullCount: number;
  trainCount: number;
  valCount: number;
}

function pct(v: number): number {
  return parseFloat((v * 100).toFixed(1));
}

function Tip({ active, payload, label }: {
  active?: boolean;
  payload?: { name: string; value: number; color: string; payload: Row }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  const counts: Record<string, number> = {
    full: row.fullCount, train: row.trainCount, val: row.valCount,
  };
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
      <p className="text-neutral-400 mb-1.5 capitalize">{label} activity</p>
      {payload.map((item) => (
        <div key={item.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: item.color }} />
          <span className="text-neutral-300">{item.name}:</span>
          <span className="text-white font-semibold">
            {item.value.toFixed(1)}% <span className="text-neutral-500">({counts[item.name]})</span>
          </span>
        </div>
      ))}
    </div>
  );
}

export function AgentDatasetDistributionChart({ report }: { report: DataQualityReport }) {
  const rows: Row[] = BINS.map((b) => ({
    bin: b,
    full: pct(report.full_distribution[b].share),
    train: pct(report.train_distribution[b].share),
    val: pct(report.val_distribution[b].share),
    fullCount: report.full_distribution[b].count,
    trainCount: report.train_distribution[b].count,
    valCount: report.val_distribution[b].count,
  }));

  return (
    <div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 5, right: 12, left: -8, bottom: 5 }} barCategoryGap="24%" barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
            <XAxis
              dataKey="bin"
              tick={{ fill: '#a3a3a3', fontSize: 11, fontFamily: 'monospace' }}
              axisLine={{ stroke: '#404040' }}
              tickLine={false}
              tickFormatter={(v: string) => v.charAt(0).toUpperCase() + v.slice(1)}
            />
            <YAxis
              tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
              axisLine={{ stroke: '#404040' }}
              tickLine={false}
              tickFormatter={(v: number) => `${v}%`}
            />
            <Tooltip content={<Tip />} cursor={{ fill: '#ffffff08' }} />
            <Bar dataKey="full" name="full" fill={SPLIT_COLORS.full} radius={[2, 2, 0, 0]} maxBarSize={26} />
            <Bar dataKey="train" name="train" fill={SPLIT_COLORS.train} radius={[2, 2, 0, 0]} maxBarSize={26} />
            <Bar dataKey="val" name="val" fill={SPLIT_COLORS.val} radius={[2, 2, 0, 0]} maxBarSize={26} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center gap-4 mt-1 px-1">
        {(['full', 'train', 'val'] as const).map((k) => (
          <div key={k} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: SPLIT_COLORS[k] }} />
            <span className="text-[10px] text-neutral-500 font-mono">{k}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
