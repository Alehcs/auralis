import { useState, useEffect, useRef } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { getLogs } from '@/lib/api';
import type { LogEntry } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

// ---------------------------------------------------------------------------
// Log line parser — extracts timestamp, level, module, message
// ---------------------------------------------------------------------------

interface ParsedLine {
  raw:       string;
  lineNo:    number;
  timestamp: string | null;
  level:     'INFO' | 'WARNING' | 'ERROR' | 'DEBUG' | null;
  module:    string | null;
  message:   string | null;
}

// Full structured format: [2024-01-01 12:00:00] INFO module ► message
const LOG_RE_FULL = /^\[([^\]]+)\]\s+(INFO|WARNING|ERROR|DEBUG)\s+([\w.\-/]+)\s+[►>]\s+(.+)$/;
// Partial: timestamp + level anywhere
const LOG_RE_TS   = /^\[([^\]]+)\]\s+(INFO|WARNING|ERROR|DEBUG)\s+(.*)$/;
// Level keyword anywhere in line
const LEVEL_RE    = /\b(INFO|WARNING|ERROR|DEBUG)\b/;
// Timestamp anywhere
const TS_RE       = /\[(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\]]*)\]/;

function parseLine(raw: string, idx: number): ParsedLine {
  // Try full structured
  let m = raw.match(LOG_RE_FULL);
  if (m) return { raw, lineNo: idx + 1, timestamp: m[1], level: m[2] as ParsedLine['level'], module: m[3], message: m[4] };

  // Try timestamp + level (no module/arrow)
  m = raw.match(LOG_RE_TS);
  if (m) return { raw, lineNo: idx + 1, timestamp: m[1], level: m[2] as ParsedLine['level'], module: null, message: m[3] };

  // Detect level keyword anywhere
  const lm = raw.match(LEVEL_RE);
  const tm = raw.match(TS_RE);
  if (lm) return {
    raw, lineNo: idx + 1,
    timestamp: tm ? tm[1] : null,
    level: lm[1] as ParsedLine['level'],
    module: null,
    message: raw,
  };

  return { raw, lineNo: idx + 1, timestamp: null, level: null, module: null, message: null };
}

function levelColor(level: ParsedLine['level']): string {
  if (level === 'ERROR')   return 'text-red-400';
  if (level === 'WARNING') return 'text-amber-400';
  if (level === 'DEBUG')   return 'text-neutral-500';
  return 'text-green-400';
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ExecutionLogs() {
  const { t } = useLanguage();
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [activeFile, setActiveFile] = useState<string>('');
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const fetchLogs = () => {
    setLoading(true);
    setError(null);
    getLogs()
      .then((entries) => {
        setLogEntries(entries);
        if (entries.length > 0) setActiveFile((prev) => prev || entries[0].filename);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchLogs(); }, []);

  useEffect(() => {
    if (terminalRef.current)
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
  }, [activeFile, logEntries]);

  const activeLog = logEntries.find((e) => e.filename === activeFile);

  // Export current log as .txt
  const handleExport = () => {
    if (!activeLog) return;
    const blob = new Blob([activeLog.lines.join('\n')], { type: 'text/plain' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = activeLog.filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="px-5 py-4 flex items-center justify-between border-b border-neutral-800">
        <div className="flex items-center gap-2.5">
          {/* Terminal icon */}
          <span className="text-orange-400 font-mono font-bold text-[15px] leading-none">{'> _'}</span>
          <span className="text-[15px] font-semibold text-white">{t.logs.title}</span>
        </div>
        <button
          onClick={handleExport}
          disabled={!activeLog}
          className="flex items-center gap-1.5 text-[12px] text-neutral-400 hover:text-white disabled:text-neutral-700 transition-colors border border-neutral-700 hover:border-neutral-500 rounded-lg px-3 py-1.5"
        >
          <Download className="w-3.5 h-3.5" />
          {t.logs.export}
        </button>
      </div>

      {/* ── File tabs ──────────────────────────────────────────── */}
      <div className="flex gap-1 px-5 pt-3 border-b border-neutral-800 overflow-x-auto">
        {logEntries.map((entry) => {
          const active = activeFile === entry.filename;
          return (
            <button
              key={entry.filename}
              onClick={() => setActiveFile(entry.filename)}
              className={`pb-2.5 px-1 text-[12px] font-mono whitespace-nowrap border-b-2 transition-colors ${
                active
                  ? 'border-orange-500 text-orange-400'
                  : 'border-transparent text-neutral-500 hover:text-neutral-300'
              }`}
            >
              {entry.filename}
            </button>
          );
        })}
        {logEntries.length === 0 && !loading && (
          <span className="pb-2.5 px-1 text-[12px] font-mono text-neutral-600">{t.logs.noFiles}</span>
        )}
      </div>

      {/* ── Terminal body ──────────────────────────────────────── */}
      <div
        ref={terminalRef}
        className="bg-[#0a0a0a] overflow-y-auto font-mono text-xs leading-6 max-h-[520px] min-h-[280px] p-4"
      >
        {loading ? (
          <div className="flex items-center gap-2 text-neutral-600">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>{t.logs.loading}</span>
          </div>
        ) : error ? (
          <div className="text-red-400">{error}</div>
        ) : activeLog && activeLog.lines.length > 0 ? (
          activeLog.lines.map((raw, idx) => {
            const p = parseLine(raw, idx);

            if (!p.level) {
              // No level detected — plain line, show in readable white-ish
              return (
                <div key={idx} className="flex gap-3 hover:bg-white/[0.02] px-1 rounded">
                  <span className="text-neutral-700 select-none w-7 text-right flex-shrink-0">
                    {String(p.lineNo).padStart(3, '0')}
                  </span>
                  <span className="text-neutral-300">{raw || ' '}</span>
                </div>
              );
            }

            return (
              <div key={idx} className="flex gap-3 hover:bg-white/[0.02] px-1 rounded">
                {/* Line number */}
                <span className="text-neutral-700 select-none w-7 text-right flex-shrink-0">
                  {String(p.lineNo).padStart(3, '0')}
                </span>
                {/* Timestamp */}
                <span className="text-cyan-500 flex-shrink-0">[{p.timestamp}]</span>
                {/* Level */}
                <span className={`${levelColor(p.level)} w-[52px] flex-shrink-0`}>
                  {p.level}
                </span>
                {/* Module */}
                <span className="text-neutral-400 flex-shrink-0">{p.module}</span>
                {/* Arrow */}
                <span className="text-neutral-600 flex-shrink-0">►</span>
                {/* Message */}
                <span className="text-neutral-200 break-all">{p.message}</span>
              </div>
            );
          })
        ) : (
          <div className="text-neutral-600">{t.logs.noContent}</div>
        )}
      </div>
    </div>
  );
}
