/**
 * Bandit behaviour over the 50 deterministic rounds:
 *  - how often each action (A1–A7) was selected;
 *  - the cumulative heuristic regret curve.
 *
 * Regret is measured against the best heuristic utility, NOT against any
 * real-world model gain. The run is deterministic (epsilon-greedy, seed 42).
 */

import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import type { ActiveLearningReport } from '@/lib/types';

const ACTION_IDS = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7'];
const HIGHLIGHT = '#a78bfa';
const NEUTRAL = '#525252';

function DistTip({ active, payload, label }: {
  active?: boolean; payload?: { value: number }[]; label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
      <span className="text-neutral-300">{label}: </span>
      <span className="text-white font-semibold">{payload[0].value} rounds</span>
    </div>
  );
}

function RegretTip({ active, payload, label }: {
  active?: boolean; payload?: { value: number }[]; label?: number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
      <span className="text-neutral-300">round {label}: </span>
      <span className="text-rose-300 font-semibold">{payload[0].value.toFixed(3)}</span>
    </div>
  );
}

export function AgentActionDistribution({ report }: { report: ActiveLearningReport }) {
  const bestId = report.best_recommendation.action_id;
  const distRows = ACTION_IDS.map((id) => ({
    action: id,
    count: report.action_distribution[id] ?? 0,
  }));
  const regretRows = report.cumulative_regret.map((v, i) => ({ round: i, regret: v }));
  const hasRegret = regretRows.length > 0;

  return (
    <div className="space-y-4">
      <div>
        <div className="text-[11px] text-neutral-500 font-mono mb-1.5">
          Selected action per round · {report.n_rounds} rounds · ε={report.epsilon} · seed={report.seed}
        </div>
        <div className="h-44">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distRows} margin={{ top: 5, right: 12, left: -12, bottom: 5 }} barCategoryGap="26%">
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
              <XAxis
                dataKey="action"
                tick={{ fill: '#a3a3a3', fontSize: 10, fontFamily: 'monospace' }}
                axisLine={{ stroke: '#404040' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                axisLine={{ stroke: '#404040' }}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip content={<DistTip />} cursor={{ fill: '#ffffff08' }} />
              <Bar dataKey="count" radius={[2, 2, 0, 0]} maxBarSize={30}>
                {distRows.map((r) => (
                  <Cell key={r.action} fill={r.action === bestId ? HIGHLIGHT : NEUTRAL} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {hasRegret && (
        <div>
          <div className="text-[11px] text-neutral-500 font-mono mb-1.5">
            Cumulative heuristic regret (vs best utility — not real-world model gain)
          </div>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={regretRows} margin={{ top: 5, right: 12, left: -12, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                <XAxis
                  dataKey="round"
                  tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={{ stroke: '#404040' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={{ stroke: '#404040' }}
                  tickLine={false}
                  tickFormatter={(v: number) => v.toFixed(1)}
                />
                <Tooltip content={<RegretTip />} cursor={{ stroke: '#404040' }} />
                <Line type="monotone" dataKey="regret" stroke="#fb7185" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
