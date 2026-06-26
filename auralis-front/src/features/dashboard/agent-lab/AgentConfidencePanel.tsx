/**
 * Evidence panel for the Active Learning Agent.
 *
 * Renders the normalised audit-need state vector that drives the bandit reward,
 * as mini bars in [0, 1]. This exposes *why* an action scores highly — it is the
 * evidence behind a decision-support recommendation, not a performance metric.
 */

const PROXY_KEYS = new Set(['uncertainty_need_proxy', 'xai_risk_proxy']);

function prettyLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\bneed\b/i, 'need')
    .replace(/\bproxy\b/i, '(proxy)');
}

function barColor(key: string, v: number): string {
  if (PROXY_KEYS.has(key)) return '#a78bfa';        // proxy signals → violet
  if (v >= 0.66) return '#f59e0b';                   // strong need → amber
  if (v >= 0.33) return '#38bdf8';                   // moderate → sky
  return '#525252';                                  // low → neutral
}

export function AgentConfidencePanel({ stateVector }: { stateVector: Record<string, number> }) {
  const entries = Object.entries(stateVector);
  if (!entries.length) {
    return <div className="text-[12px] text-neutral-500">No state vector available.</div>;
  }
  return (
    <div className="space-y-2">
      {entries.map(([key, value]) => {
        const v = Math.max(0, Math.min(1, value));
        return (
          <div key={key} className="flex items-center gap-3">
            <div className="w-[190px] flex-shrink-0 text-[11px] text-neutral-400 font-mono truncate" title={key}>
              {prettyLabel(key)}
            </div>
            <div className="flex-1 h-2 rounded-full bg-neutral-800 overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${v * 100}%`, background: barColor(key, v) }}
              />
            </div>
            <div className="w-10 flex-shrink-0 text-right text-[11px] text-neutral-300 font-mono">
              {value.toFixed(2)}
            </div>
          </div>
        );
      })}
      <p className="text-[10px] text-neutral-600 font-mono pt-1">
        Values normalised to [0,1]. Proxy signals (violet) are placeholders, not measured quantities.
      </p>
    </div>
  );
}
