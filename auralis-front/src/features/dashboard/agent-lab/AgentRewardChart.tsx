/**
 * Decision-support utility per candidate action (A1–A7).
 *
 * Bars are heuristic reward = 0.4·error + 0.3·underrepresentation + 0.2·
 * uncertainty + 0.1·xai_risk, computed from the current audit signals. This is
 * NOT measured model improvement. The best action is highlighted; A5 (tail
 * follow-up) stays visible alongside it.
 */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import type { ActiveLearningReport, BanditActionUtility } from '@/lib/types';

const HIGHLIGHT = '#f59e0b';
const NEUTRAL = '#525252';

function Tip({ active, payload }: {
  active?: boolean;
  payload?: { payload: BanditActionUtility }[];
}) {
  if (!active || !payload?.length) return null;
  const a = payload[0].payload;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg max-w-[260px]">
      <p className="text-white font-semibold mb-0.5">{a.action_id} · {a.action_name}</p>
      <p className="text-neutral-400 mb-1.5 leading-snug font-sans">{a.description}</p>
      <div className="flex items-center gap-2">
        <span className="text-neutral-400">utility:</span>
        <span className="text-amber-300 font-semibold">{a.utility.toFixed(4)}</span>
      </div>
    </div>
  );
}

export function AgentRewardChart({ report }: { report: ActiveLearningReport }) {
  const bestId = report.best_recommendation.action_id;
  // Keep backend order (sorted by utility desc) for a clean ranked chart.
  const rows = report.action_utilities.map((a) => ({ ...a, utilityRounded: parseFloat(a.utility.toFixed(4)) }));

  return (
    <div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" margin={{ top: 5, right: 16, left: 6, bottom: 5 }} barCategoryGap="22%">
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
              dataKey="action_id"
              tick={{ fill: '#a3a3a3', fontSize: 11, fontFamily: 'monospace' }}
              axisLine={false}
              tickLine={false}
              width={34}
            />
            <Tooltip content={<Tip />} cursor={{ fill: '#ffffff08' }} />
            <Bar dataKey="utilityRounded" radius={[0, 2, 2, 0]} maxBarSize={18}>
              {rows.map((r) => (
                <Cell key={r.action_id} fill={r.action_id === bestId ? HIGHLIGHT : NEUTRAL} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center gap-4 mt-1 px-1">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: HIGHLIGHT }} />
          <span className="text-[10px] text-neutral-500 font-mono">best recommendation ({bestId})</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: NEUTRAL }} />
          <span className="text-[10px] text-neutral-500 font-mono">other actions</span>
        </div>
      </div>
    </div>
  );
}
