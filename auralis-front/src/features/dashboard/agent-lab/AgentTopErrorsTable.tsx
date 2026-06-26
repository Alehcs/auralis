/**
 * Top high-error hold-out samples.
 *
 * These concentrate in the SI > 2.0 tail/extreme region — the audit's main
 * weakness signal. Rows with real SI > 2.0 are tagged so the tail concentration
 * is visible at a glance.
 */

import type { ErrorSample } from '@/lib/types';
import { BIN_COLORS } from './AgentCard';

const TAIL_SI = 2.0;

export function AgentTopErrorsTable({ samples }: { samples: ErrorSample[] }) {
  if (!samples.length) {
    return <div className="text-[12px] text-neutral-500">No hold-out samples available.</div>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono min-w-[520px]">
        <thead>
          <tr className="border-b border-neutral-800">
            <th className="text-left  px-3 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">DATE</th>
            <th className="text-left  px-3 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">BIN</th>
            <th className="text-right px-3 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">REAL SI</th>
            <th className="text-right px-3 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">PRED</th>
            <th className="text-right px-3 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">|ERROR|</th>
            <th className="text-right px-3 py-2.5 text-[10px] text-neutral-500 font-medium tracking-[0.1em]">TAIL</th>
          </tr>
        </thead>
        <tbody>
          {samples.map((s, idx) => {
            const isTail = s.real > TAIL_SI;
            return (
              <tr
                key={s.filename + idx}
                className={`border-b border-neutral-800/50 ${idx % 2 === 0 ? '' : 'bg-neutral-800/20'}`}
                title={s.filename}
              >
                <td className="px-3 py-2.5 text-neutral-400">{s.date ?? '—'}</td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 capitalize text-neutral-300">
                    <span className="w-2 h-2 rounded-full inline-block" style={{ background: BIN_COLORS[s.activity_bin] }} />
                    {s.activity_bin}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right text-neutral-300">{s.real.toFixed(3)}</td>
                <td className="px-3 py-2.5 text-right text-cyan-300">{s.predicted.toFixed(3)}</td>
                <td className="px-3 py-2.5 text-right font-semibold text-red-300">{s.error.toFixed(3)}</td>
                <td className="px-3 py-2.5 text-right">
                  {isTail ? (
                    <span className="text-[10px] text-amber-300 border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 rounded">
                      SI&gt;2.0
                    </span>
                  ) : (
                    <span className="text-neutral-600">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
