import { useState, useEffect } from 'react';
import { FileText, Loader2 } from 'lucide-react';
import { getExperiments } from '@/lib/api';
import type { ExperimentEntry } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  try {
    return new Date(iso).toISOString().slice(0, 10);
  } catch {
    return iso.slice(0, 10);
  }
}

// Saved experiment artifacts do not expose live execution status.
// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ExperimentLog() {
  const { t } = useLanguage();
  const e = t.experiments;

  const [experiments, setExperiments] = useState<ExperimentEntry[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);

  useEffect(() => {
    getExperiments()
      .then(setExperiments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Show last 6 experiments (most recent first)
  const shown = experiments.slice(0, 6);

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-neutral-800 flex items-start justify-between">
        <div className="text-[15px] font-semibold text-white">{e.expHistory}</div>
        <span className="text-[10px] font-mono text-neutral-500 tracking-[0.12em]">
          {e.lastRuns.replace('{n}', String(shown.length))}
        </span>
      </div>

      {/* Body */}
      {loading ? (
        <div className="flex items-center justify-center gap-2 p-10 text-neutral-600 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin" />
          {e.loading}
        </div>
      ) : error ? (
        <div className="px-5 py-4 text-xs text-red-400 font-mono">{error}</div>
      ) : shown.length === 0 ? (
        <div className="px-5 py-6 text-xs text-neutral-600 font-mono">{e.loading}</div>
      ) : (
        <div className="divide-y divide-neutral-800/60">
          {shown.map((exp) => {
            const mae    = exp.metrics.final_mae;
            const expId  = exp.run_id.length > 12 ? exp.run_id.slice(0, 12) : exp.run_id;

            return (
              <div key={exp.run_id} className="flex items-center gap-3 px-5 py-4">
                {/* Status icon */}
                <div className="w-8 h-8 rounded-full border border-neutral-700 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-4 h-4 text-neutral-400" />
                </div>

                {/* Name + meta */}
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] text-white font-medium truncate">
                    {exp.run_name}
                  </div>
                  <div className="text-[10px] text-neutral-500 font-mono mt-0.5">
                    {expId.toUpperCase()} · {formatDate(exp.date)}
                    <span className="block">{exp.evidence_status?.startsWith('clean_observation') ? 'V3.1 MC T=20 · selection validation' : 'Historical artifact · protocols differ'}</span>
                  </div>
                </div>

                {/* MAE */}
                <div className="text-right flex-shrink-0">
                  <div className="text-[9px] text-neutral-500 font-mono tracking-[0.1em]">{e.mae_label} {exp.evidence_status?.startsWith('clean_observation') ? '(SI pp)' : '(recorded)'}</div>
                  <div className="text-[15px] font-mono font-bold text-neutral-300">
                    {mae.toFixed(4)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
