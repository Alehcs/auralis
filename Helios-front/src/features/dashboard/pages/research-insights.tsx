import { GlobalMetrics }          from '../components/global-metrics';
import { KFoldResults }           from '../components/kfold-results';
import { ModelComparisonChart, ModelComparisonTable } from '../components/architecture-comparison';
import { ExperimentLog }          from '../components/experiment-log';
import { PredictedVsActual }      from '../components/predicted-vs-actual';
import { XAIFaithfulness }        from '../components/xai-faithfulness';

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function ResearchInsights() {
  return (
    <div className="space-y-4">

      {/* ── Row 1: 3 metric cards ────────────────────────────────── */}
      <GlobalMetrics />

      {/* ── Row 2: scatter plot | model comparison chart ─────────── */}
      <div className="grid grid-cols-[1fr_380px] gap-4">
        <PredictedVsActual />
        <ModelComparisonChart />
      </div>

      {/* ── Row 3: model table (full width) ──────────────────────── */}
      <ModelComparisonTable />

      {/* ── Row 4: K-Fold | Experiment history ───────────────────── */}
      <div className="grid grid-cols-2 gap-4">
        <KFoldResults />
        <ExperimentLog />
      </div>

      {/* ── Row 5: XAI Faithfulness (full width) ─────────────────── */}
      <XAIFaithfulness />

    </div>
  );
}
