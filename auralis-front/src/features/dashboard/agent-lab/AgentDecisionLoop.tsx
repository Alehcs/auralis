/**
 * Agent decision loop — a compact, teaching-oriented visual of the contextual
 * bandit pipeline:
 *
 *   Audit data → State vector → ε-greedy policy → Selected action → Heuristic reward
 *
 * Built for clarity (e.g. a Systems Intelligence course): each stage is labelled
 * with the concept it represents — state, policy, action, reward. Every numeric
 * value comes from the live Active Learning sub-report; only the stage labels are
 * static. Nothing here is retraining or measured model improvement.
 */

import { Fragment } from 'react';
import { Database, Layers, Shuffle, Target, Award, ArrowRight } from 'lucide-react';
import type { ActiveLearningReport } from '@/lib/types';
import { AgentCard, MutedNote } from './AgentCard';

interface Step {
  label: string;
  Icon: typeof Database;
  value: string;
  sub: string;
}

export function AgentDecisionLoop({ report }: { report: ActiveLearningReport }) {
  const best = report.best_recommendation;
  const stateDims = Object.keys(report.state_vector).length;

  // All values below are read from the live full-report; labels are static.
  const steps: Step[] = [
    {
      label: 'AUDIT DATA',
      Icon: Database,
      value: 'Hold-out results',
      sub: 'Coronium V3 PRO audit',
    },
    {
      label: 'STATE',
      Icon: Layers,
      value: `${stateDims} signals`,
      sub: 'audit-need vector',
    },
    {
      label: 'POLICY',
      Icon: Shuffle,
      value: `ε = ${report.epsilon}`,
      sub: `${report.n_rounds} rounds · seed ${report.seed}`,
    },
    {
      label: 'ACTION',
      Icon: Target,
      value: best.action_id,
      sub: best.action_name,
    },
    {
      label: 'REWARD',
      Icon: Award,
      value: best.utility.toFixed(3),
      sub: 'heuristic utility',
    },
  ];

  return (
    <AgentCard
      title="Agent decision loop"
      subtitle="How the contextual bandit turns audit data into a recommended action"
    >
      <div className="flex flex-col sm:flex-row sm:items-stretch gap-2">
        {steps.map((s, i) => (
          <Fragment key={s.label}>
            <div className="flex-1 min-w-0 rounded-lg border border-neutral-800 bg-neutral-950/40 p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <s.Icon className="w-3.5 h-3.5 text-neutral-500 flex-shrink-0" />
                <span className="text-[9px] text-neutral-500 tracking-[0.16em] font-mono">{s.label}</span>
              </div>
              <div className="text-[13px] font-semibold text-white truncate" title={s.value}>{s.value}</div>
              <div className="text-[10.5px] text-neutral-500 leading-snug mt-0.5 break-words">{s.sub}</div>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight className="w-4 h-4 text-neutral-600 flex-shrink-0 self-center rotate-90 sm:rotate-0" />
            )}
          </Fragment>
        ))}
      </div>

      <div className="mt-3">
        <MutedNote text="State → policy → action → reward · read-only decision support · heuristic reward, no retraining." />
      </div>
    </AgentCard>
  );
}
