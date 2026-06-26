/**
 * Coordinator / Full Report panel.
 *
 * Composes the audit brief: overall audit confidence, dataset health, model
 * weakness, the recommended data priority, next steps, and consolidated
 * limitations. All framing is audit / decision-support — no retraining is
 * performed and nothing here is evidence of real-world model improvement.
 */

import { Database, Activity, Compass, ListChecks } from 'lucide-react';
import type { FullAgentReport } from '@/lib/types';
import { ConfidenceBadge, LimitationsList } from './AgentCard';

function SummaryBlock({ Icon, title, body }: { Icon: typeof Database; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 p-3.5">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon className="w-3.5 h-3.5 text-neutral-500" />
        <span className="text-[10px] text-neutral-500 tracking-[0.14em] font-mono">{title}</span>
      </div>
      <p className="text-[12.5px] text-neutral-300 leading-snug">{body}</p>
    </div>
  );
}

export function AgentReportPanel({ report }: { report: FullAgentReport }) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 flex items-start justify-between gap-3 border-b border-neutral-800">
        <div>
          <div className="text-[15px] font-semibold text-white">{report.agent_name}</div>
          <div className="text-[11px] text-neutral-500 mt-0.5">
            Combined read-only audit brief · generated {new Date(report.generated_at).toLocaleString()}
          </div>
        </div>
        <ConfidenceBadge confidence={report.confidence} />
      </div>

      <div className="p-5 space-y-4">
        <p className="text-[13px] text-neutral-300 leading-relaxed">{report.summary}</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <SummaryBlock Icon={Database} title="DATASET HEALTH" body={report.dataset_health_summary} />
          <SummaryBlock Icon={Activity} title="MODEL WEAKNESS" body={report.model_weakness_summary} />
          <SummaryBlock Icon={Compass} title="RECOMMENDED DATA PRIORITY" body={report.active_learning_recommendation} />
          <SummaryBlock Icon={Activity} title="XAI CAUTION" body={report.xai_caution_summary} />
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <ListChecks className="w-3.5 h-3.5 text-neutral-500" />
            <span className="text-[10px] text-neutral-500 tracking-[0.14em] font-mono">RECOMMENDED NEXT STEPS</span>
          </div>
          <ol className="space-y-1.5">
            {report.recommended_next_steps.map((step, i) => (
              <li key={i} className="flex gap-2.5 text-[12.5px] text-neutral-300 leading-snug">
                <span className="flex-shrink-0 w-5 h-5 rounded-md bg-neutral-800 text-neutral-400 text-[11px] font-mono flex items-center justify-center">
                  {i + 1}
                </span>
                <span className="pt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        <LimitationsList limitations={report.limitations} />
      </div>
    </div>
  );
}
