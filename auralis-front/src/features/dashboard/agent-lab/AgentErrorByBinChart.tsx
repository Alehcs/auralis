/**
 * Error by activity bin: MAE and RMSE per bin, plus signed residual means.
 *
 * The narrative this supports: bin-level MAE is nearly flat — the model does not
 * fail one whole activity band. The real weak spot (the SI > 2.0 tail) is shown
 * separately in the top-errors table, not here.
 */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { ErrorAnalysisReport, ActivityBin } from '@/lib/types';

const BINS: ActivityBin[] = ['low', 'medium', 'high'];

interface Row {
  bin: string;
  mae: number;
  rmse: number;
  residual: number;
}

function Tip({ active, payload, label }: {
  active?: boolean;
  payload?: { name: string; value: number; color: string; payload: Row }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
      <p className="text-neutral-400 mb-1.5 capitalize">{label} activity</p>
      {payload.map((item) => (
        <div key={item.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: item.color }} />
          <span className="text-neutral-300">{item.name}:</span>
          <span className="text-white font-semibold">{item.value.toFixed(4)}</span>
        </div>
      ))}
      <div className="flex items-center gap-2 mt-1 pt-1 border-t border-neutral-800">
        <span className="text-neutral-400">residual μ:</span>
        <span className={row.residual < 0 ? 'text-orange-300' : 'text-sky-300'}>
          {row.residual >= 0 ? '+' : ''}{row.residual.toFixed(4)}
        </span>
      </div>
    </div>
  );
}

export function AgentErrorByBinChart({ report }: { report: ErrorAnalysisReport }) {
  const rows: Row[] = BINS.map((b) => ({
    bin: b,
    mae: report.mae_by_bin[b],
    rmse: report.rmse_by_bin[b],
    residual: report.residual_mean_by_bin[b],
  }));

  // Tight domain so the "nearly flat" MAE is honestly visible (not exaggerated).
  const maxVal = Math.max(...rows.flatMap((r) => [r.mae, r.rmse]));
  const domainMax = parseFloat((maxVal * 1.25).toFixed(3));

  return (
    <div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 5, right: 12, left: -4, bottom: 5 }} barCategoryGap="28%" barGap={3}>
            <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
            <XAxis
              dataKey="bin"
              tick={{ fill: '#a3a3a3', fontSize: 11, fontFamily: 'monospace' }}
              axisLine={{ stroke: '#404040' }}
              tickLine={false}
              tickFormatter={(v: string) => v.charAt(0).toUpperCase() + v.slice(1)}
            />
            <YAxis
              domain={[0, domainMax]}
              tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
              axisLine={{ stroke: '#404040' }}
              tickLine={false}
              tickFormatter={(v: number) => v.toFixed(2)}
            />
            <Tooltip content={<Tip />} cursor={{ fill: '#ffffff08' }} />
            <Bar dataKey="mae" name="MAE" fill="#f59e0b" radius={[2, 2, 0, 0]} maxBarSize={34} />
            <Bar dataKey="rmse" name="RMSE" fill="#38bdf8" radius={[2, 2, 0, 0]} maxBarSize={34} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-between mt-1 px-1">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-400 inline-block" />
            <span className="text-[10px] text-neutral-500 font-mono">MAE</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-sky-400 inline-block" />
            <span className="text-[10px] text-neutral-500 font-mono">RMSE</span>
          </div>
        </div>
        <span className="text-[10px] text-neutral-500 font-mono">
          MAE spread {report.mae_spread.toFixed(4)} · {report.error_is_flat ? 'nearly flat' : 'uneven'}
        </span>
      </div>
    </div>
  );
}
