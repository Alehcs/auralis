/**
 * Shared presentational primitives for the Agent Lab.
 *
 * Everything here is read-only display: card shells, the audit-confidence pill,
 * severity-coded finding/limitation lists, and the global caution badge. Copy is
 * deliberately framed as audit / decision-support, never as model improvement.
 */

import type { ReactNode } from 'react';
import { AlertTriangle, Info, ShieldAlert } from 'lucide-react';
import type { AgentFinding, AgentLimitation, ActivityBin, Severity } from '@/lib/types';

/** Per-bin colours, matching the existing classification palette. */
export const BIN_COLORS: Record<ActivityBin, string> = {
  low: '#22c55e',
  medium: '#f97316',
  high: '#ef4444',
};

/** Per-split colours for distribution comparisons. */
export const SPLIT_COLORS = {
  full: '#f59e0b',
  train: '#38bdf8',
  val: '#a78bfa',
} as const;

const SEVERITY_STYLE: Record<Severity, { dot: string; text: string; Icon: typeof Info }> = {
  info:    { dot: 'bg-sky-400',   text: 'text-sky-300',    Icon: Info },
  notice:  { dot: 'bg-amber-400', text: 'text-amber-300',  Icon: ShieldAlert },
  warning: { dot: 'bg-red-400',   text: 'text-red-300',    Icon: AlertTriangle },
};

// ---------------------------------------------------------------------------
// Card shell
// ---------------------------------------------------------------------------

interface AgentCardProps {
  title: string;
  subtitle?: string;
  /** Optional content rendered on the right of the header (e.g. a badge). */
  headerRight?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function AgentCard({ title, subtitle, headerRight, children, className }: AgentCardProps) {
  return (
    <div className={`bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden ${className ?? ''}`}>
      <div className="px-5 py-4 flex items-start justify-between gap-3 border-b border-neutral-800">
        <div className="min-w-0">
          <div className="text-[15px] font-semibold text-white">{title}</div>
          {subtitle && <div className="text-[11px] text-neutral-500 mt-0.5">{subtitle}</div>}
        </div>
        {headerRight}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Audit-confidence pill (NOT prediction accuracy)
// ---------------------------------------------------------------------------

export function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const tone =
    confidence >= 0.8 ? 'text-green-300 border-green-500/30 bg-green-500/10'
    : confidence >= 0.6 ? 'text-amber-300 border-amber-500/30 bg-amber-500/10'
    : 'text-neutral-300 border-neutral-600 bg-neutral-800';
  return (
    <span
      title="Audit confidence — the agent's self-assessed certainty in this audit, not model prediction accuracy."
      className={`text-[10px] font-mono px-2.5 py-1 rounded-lg border whitespace-nowrap ${tone}`}
    >
      audit confidence {pct}%
    </span>
  );
}

// ---------------------------------------------------------------------------
// Global caution badge
// ---------------------------------------------------------------------------

export function CautionBadge({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3.5 py-2.5">
      <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
      <span className="text-[12px] text-amber-200/90 leading-snug">{text}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Findings & limitations
// ---------------------------------------------------------------------------

export function FindingsList({ findings }: { findings: AgentFinding[] }) {
  if (!findings.length) return null;
  return (
    <ul className="space-y-2.5">
      {findings.map((f) => {
        const s = SEVERITY_STYLE[f.severity] ?? SEVERITY_STYLE.info;
        return (
          <li key={f.key} className="flex gap-2.5">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.dot}`} />
            <div className="min-w-0">
              <div className={`text-[12.5px] font-medium ${s.text}`}>{f.label}</div>
              <div className="text-[12px] text-neutral-400 leading-snug">{f.detail}</div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export function LimitationsList({ limitations }: { limitations: AgentLimitation[] }) {
  if (!limitations.length) return null;
  return (
    <div className="mt-4 pt-3 border-t border-neutral-800">
      <div className="text-[10px] text-neutral-500 tracking-[0.14em] font-mono mb-1.5">LIMITATIONS</div>
      <ul className="space-y-1">
        {limitations.map((l) => (
          <li key={l.key} className="text-[11px] text-neutral-500 leading-snug flex gap-1.5">
            <span className="text-neutral-600">·</span>
            <span>{l.detail}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
