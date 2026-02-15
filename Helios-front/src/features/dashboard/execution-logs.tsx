import { useState, useEffect, useRef } from 'react';
import { RefreshCw, Loader2 } from 'lucide-react';
import { getLogs } from '@/lib/api';
import type { LogEntry } from '@/lib/types';

export function ExecutionLogs() {
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [activeFile, setActiveFile] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const fetchLogs = () => {
    setLoading(true);
    setError(null);
    getLogs()
      .then((entries) => {
        setLogEntries(entries);
        if (entries.length > 0 && !activeFile) {
          setActiveFile(entries[0].filename);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  // Auto-scroll terminal to bottom on content change
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [activeFile, logEntries]);

  const activeLog = logEntries.find((e) => e.filename === activeFile);

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      {/* Header */}
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">System Logs</h2>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              Last 50 lines per log file | {logEntries.length} files available
            </p>
          </div>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="flex items-center space-x-1.5 text-[11px] text-blue-400 hover:text-blue-300 disabled:text-neutral-600 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-950 border-b border-red-900 px-4 py-2 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Log file tabs */}
      <div className="flex border-b border-neutral-800 bg-neutral-900/50 overflow-x-auto">
        {logEntries.map((entry) => (
          <button
            key={entry.filename}
            onClick={() => setActiveFile(entry.filename)}
            className={`px-4 py-2 text-xs font-mono whitespace-nowrap border-b-2 transition-colors ${activeFile === entry.filename
                ? 'border-blue-500 text-white bg-neutral-900'
                : 'border-transparent text-neutral-500 hover:text-neutral-300'
              }`}
          >
            {entry.filename}
          </button>
        ))}
      </div>

      {/* Terminal output */}
      <div
        ref={terminalRef}
        className="bg-black p-4 overflow-y-auto font-mono text-xs leading-5 max-h-[600px] min-h-[300px]"
      >
        {loading ? (
          <div className="flex items-center space-x-2 text-neutral-600">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>Loading logs...</span>
          </div>
        ) : activeLog && activeLog.lines.length > 0 ? (
          activeLog.lines.map((line, idx) => {
            // Color-code log levels
            let lineClass = 'text-neutral-400';
            if (line.includes('ERROR')) lineClass = 'text-red-400';
            else if (line.includes('WARNING')) lineClass = 'text-yellow-400';
            else if (line.includes('INFO')) lineClass = 'text-green-400';

            return (
              <div key={idx} className={`${lineClass} hover:bg-neutral-900/50`}>
                <span className="text-neutral-700 select-none mr-3">{String(idx + 1).padStart(3, ' ')}</span>
                {line}
              </div>
            );
          })
        ) : (
          <div className="text-neutral-600">No log content available.</div>
        )}
      </div>
    </div>
  );
}
