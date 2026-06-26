/**
 * Auralis Agent Lab — read-only scientific audit dashboard.
 *
 * Fetches /api/agents/full-report ONCE and renders the whole page from its
 * embedded sub-reports (data_quality, error_analysis, xai_review,
 * active_learning). This avoids duplicated metrics and inconsistent loading
 * states. The agents audit and recommend; they do not modify Coronium and do
 * not prove model improvement.
 */

import { useEffect, useState } from 'react';
import { AlertTriangle, Database, Activity, Eye, Compass } from 'lucide-react';
import { getAgentFullReport } from '@/lib/api';
import type { FullAgentReport } from '@/lib/types';

import {
  AgentCard, ConfidenceBadge, CautionBadge, FindingsList, LimitationsList, BIN_COLORS,
} from './AgentCard';
import { AgentReportPanel } from './AgentReportPanel';
import { AgentDatasetDistributionChart } from './AgentDatasetDistributionChart';
import { AgentErrorByBinChart } from './AgentErrorByBinChart';
import { AgentTopErrorsTable } from './AgentTopErrorsTable';
import { AgentRewardChart } from './AgentRewardChart';
import { AgentActionDistribution } from './AgentActionDistribution';
import { AgentConfidencePanel } from './AgentConfidencePanel';

const PAGE_CAUTION =
  'Audit layer only — agents do not modify Coronium or prove model improvement. ' +
  'Read-only analysis; no retraining performed.';

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function SkeletonCard({ height = 'h-48' }: { height?: string }) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden animate-pulse">
      <div className="px-5 py-4 border-b border-neutral-800">
        <div className="h-4 w-44 bg-neutral-800 rounded" />
        <div className="h-2.5 w-64 bg-neutral-800/60 rounded mt-2" />
      </div>
      <div className={`p-5 ${height}`}>
        <div className="h-full w-full bg-neutral-800/40 rounded-lg" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small stat chip
// ---------------------------------------------------------------------------

function Chip({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 px-3 py-2">
      <div className="text-[9px] text-neutral-500 tracking-[0.14em] font-mono">{label}</div>
      <div className={`text-[13px] font-semibold mt-0.5 ${tone ?? 'text-white'}`}>{value}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function AgentLabPage() {
  const [report, setReport] = useState<FullAgentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    getAgentFullReport()
      .then((r) => { if (alive) setReport(r); })
      .catch((e) => { if (alive) setError(e.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  return (
    <div className="space-y-4">
      {/* ── Header ────────────────────────────────────────────────── */}
      <div className="space-y-3">
        <div>
          <h1 className="text-[20px] font-bold text-white tracking-tight">Auralis Agent Lab</h1>
          <p className="text-[12.5px] text-neutral-500 mt-1 max-w-3xl leading-snug">
            Read-only scientific audit agents for dataset quality, model error analysis, XAI review,
            and active-learning recommendations.
          </p>
        </div>
        <CautionBadge text={PAGE_CAUTION} />
      </div>

      {/* ── Loading ───────────────────────────────────────────────── */}
      {loading && (
        <div className="space-y-4">
          <SkeletonCard height="h-40" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <SkeletonCard /><SkeletonCard />
          </div>
          <SkeletonCard height="h-56" />
        </div>
      )}

      {/* ── Error (card-level; does not crash the dashboard) ──────── */}
      {!loading && error && (
        <div className="bg-neutral-900 border border-red-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 text-red-300">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-[14px] font-semibold">Agent Lab unavailable</span>
          </div>
          <p className="text-[12px] text-neutral-400 mt-2 font-mono">{error}</p>
          <p className="text-[12px] text-neutral-500 mt-2 leading-snug">
            The audit layer reads <code className="text-neutral-400">/api/agents/full-report</code>. Ensure the
            backend is running and the required artifacts (metadata, split, results CSV) are present. Other
            dashboard tabs are unaffected.
          </p>
        </div>
      )}

      {/* ── Content ───────────────────────────────────────────────── */}
      {!loading && !error && report && (
        <div className="space-y-4">

          {/* 1 — Coordinator / Full Report */}
          <AgentReportPanel report={report} />

          {/* 2 + 3 — Data Quality | Error Analysis */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">

            {/* Data Quality Agent */}
            <AgentCard
              title="Data Quality Agent"
              subtitle="Dataset composition and balance audit"
              headerRight={<ConfidenceBadge confidence={report.data_quality.confidence} />}
            >
              <div className="grid grid-cols-3 gap-2.5 mb-4">
                <Chip
                  label="MINORITY BIN"
                  value={report.data_quality.minority_bin}
                  tone="capitalize"
                />
                <Chip
                  label="LOW UNDERREP."
                  value={report.data_quality.low_activity_underrepresented ? 'Yes' : 'No'}
                  tone={report.data_quality.low_activity_underrepresented ? 'text-amber-300' : 'text-green-300'}
                />
                <Chip
                  label="COVERAGE"
                  value={
                    report.data_quality.date_coverage.year_min != null
                      ? `${report.data_quality.date_coverage.year_min}–${report.data_quality.date_coverage.year_max}`
                      : '—'
                  }
                />
              </div>

              {report.data_quality.low_activity_underrepresented && (
                <div className="mb-4">
                  <CautionBadge text="Low activity is the minority class — quiet-Sun / solar-minimum conditions are underrepresented relative to medium/high activity." />
                </div>
              )}

              <div className="flex items-center gap-2 mb-2">
                <Database className="w-3.5 h-3.5 text-neutral-500" />
                <span className="text-[11px] text-neutral-400 font-mono">Activity-bin distribution — full vs train vs validation (share %)</span>
              </div>
              <AgentDatasetDistributionChart report={report.data_quality} />

              <div className="mt-4 pt-3 border-t border-neutral-800">
                <FindingsList findings={report.data_quality.findings} />
              </div>
              <LimitationsList limitations={report.data_quality.limitations} />
            </AgentCard>

            {/* Error Analysis Agent */}
            <AgentCard
              title="Error Analysis Agent"
              subtitle="Hold-out error audit by activity bin"
              headerRight={<ConfidenceBadge confidence={report.error_analysis.confidence} />}
            >
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-3.5 h-3.5 text-neutral-500" />
                <span className="text-[11px] text-neutral-400 font-mono">MAE / RMSE by activity bin (log-SI)</span>
              </div>
              <AgentErrorByBinChart report={report.error_analysis} />

              {report.error_analysis.tail_extreme_count > 0 && (
                <div className="mt-4">
                  <CautionBadge
                    text={
                      `Bin-level MAE is nearly flat, but the weakness concentrates in the SI > 2.0 tail: ` +
                      `${report.error_analysis.tail_extreme_count} extreme samples, ` +
                      `tail MAE ${report.error_analysis.tail_extreme_mae?.toFixed(4) ?? '—'}. ` +
                      `This is a tail/extreme-event weakness, not a generic high-bin failure.`
                    }
                  />
                </div>
              )}

              <div className="flex items-center gap-2 mt-4 mb-2">
                <span className="text-[11px] text-neutral-400 font-mono">Top high-error hold-out samples</span>
                <span className="ml-auto inline-flex items-center gap-1.5 text-[10px] text-neutral-500">
                  {(['low', 'medium', 'high'] as const).map((b) => (
                    <span key={b} className="inline-flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full inline-block" style={{ background: BIN_COLORS[b] }} />
                      {b}
                    </span>
                  ))}
                </span>
              </div>
              <AgentTopErrorsTable samples={report.error_analysis.top_errors} />

              <div className="mt-4 pt-3 border-t border-neutral-800">
                <FindingsList findings={report.error_analysis.findings} />
              </div>
              <LimitationsList limitations={report.error_analysis.limitations} />
            </AgentCard>
          </div>

          {/* 4 — XAI Review Agent */}
          <AgentCard
            title="XAI Review Agent"
            subtitle="Explainability inventory and sampled-sweep strategy"
            headerRight={<ConfidenceBadge confidence={report.xai_review.confidence} />}
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-4">
              <Chip label="SWEEP STATUS" value={report.xai_review.sweep_status} tone="text-amber-300 capitalize" />
              <Chip
                label="FAITHFULNESS API"
                value={report.xai_review.faithfulness_endpoint_available ? 'Available' : 'Absent'}
                tone={report.xai_review.faithfulness_endpoint_available ? 'text-green-300' : 'text-neutral-400'}
              />
              <Chip label="XAI ASSETS" value={String(report.xai_review.available_assets.length)} />
              <Chip label="MODE" value="Read-only" />
            </div>

            <div className="mb-4">
              <CautionBadge text="Grad-CAM is post-hoc and non-causal. It supports inspection, not proof of physical reasoning." />
            </div>

            <div className="flex items-center gap-2 mb-2">
              <Eye className="w-3.5 h-3.5 text-neutral-500" />
              <span className="text-[11px] text-neutral-400 font-mono">Available XAI assets</span>
            </div>
            <ul className="space-y-1 mb-4">
              {report.xai_review.available_assets.map((a, i) => (
                <li key={i} className="text-[11.5px] text-neutral-400 font-mono leading-snug flex gap-2">
                  <span className="text-neutral-600">›</span>{a}
                </li>
              ))}
            </ul>

            <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 p-3.5">
              <div className="text-[10px] text-neutral-500 tracking-[0.14em] font-mono mb-1.5">SAMPLED SWEEP STRATEGY</div>
              <p className="text-[12px] text-neutral-300 leading-snug">{report.xai_review.sampled_strategy_recommendation}</p>
            </div>

            <div className="mt-4 pt-3 border-t border-neutral-800">
              <FindingsList findings={report.xai_review.findings} />
            </div>
            <LimitationsList limitations={report.xai_review.limitations} />
          </AgentCard>

          {/* 5 — Active Learning Agent */}
          <AgentCard
            title="Active Learning Agent"
            subtitle="Deterministic contextual bandit · recommended data priority"
            headerRight={<ConfidenceBadge confidence={report.active_learning.confidence} />}
          >
            <div className="mb-4">
              <CautionBadge text="Reward is decision-support utility from current audit signals, not measured model improvement. No retraining performed." />
            </div>

            {/* Best recommendation banner */}
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3.5 mb-4">
              <div className="flex items-center gap-2 mb-1">
                <Compass className="w-4 h-4 text-amber-400" />
                <span className="text-[10px] text-amber-300/80 tracking-[0.14em] font-mono">RECOMMENDED DATA PRIORITY</span>
              </div>
              <div className="text-[14px] font-semibold text-amber-100">
                {report.active_learning.best_recommendation.action_id} · {report.active_learning.best_recommendation.action_name}
              </div>
              <p className="text-[12px] text-amber-200/80 mt-0.5 leading-snug">
                {report.active_learning.best_recommendation.description}
              </p>
              <div className="text-[11px] text-amber-300/70 font-mono mt-1">
                heuristic utility {report.active_learning.best_recommendation.utility.toFixed(4)}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div>
                <div className="text-[11px] text-neutral-400 font-mono mb-2">Decision-support utility per action (A1–A7)</div>
                <AgentRewardChart report={report.active_learning} />
              </div>
              <div>
                <AgentActionDistribution report={report.active_learning} />
              </div>
            </div>

            <div className="mt-5">
              <div className="text-[11px] text-neutral-400 font-mono mb-2">Audit-need state vector (evidence behind the recommendation)</div>
              <AgentConfidencePanel stateVector={report.active_learning.state_vector} />
            </div>

            <div className="mt-4 pt-3 border-t border-neutral-800">
              <FindingsList findings={report.active_learning.findings} />
            </div>
            <LimitationsList limitations={report.active_learning.limitations} />
          </AgentCard>

        </div>
      )}
    </div>
  );
}
