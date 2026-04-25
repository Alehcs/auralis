import { useState, useEffect } from 'react';
import { Bell, RefreshCw, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '@/lib/i18n/language-context';

export function ScientificHeader() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const dateStr = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';

  return (
    <header className="h-[56px] flex-shrink-0 bg-[#0d0d0d] border-b border-neutral-800/60 px-6 flex items-center gap-4">

      {/* ── Left: Title + breadcrumb ───────────────────────────── */}
      <div className="flex-shrink-0">
        <button onClick={() => navigate('/')} className="text-left group">
          <div className="text-[13px] font-semibold text-white group-hover:text-neutral-200 transition-colors leading-tight">
            Solar Activity Prediction Dashboard
          </div>
          <div className="flex items-center gap-1 text-[11px] text-neutral-500 mt-[1px]">
            <span>HeliosPipeline</span>
            <span className="text-neutral-700">›</span>
            <span>SDO-HMI Analysis</span>
          </div>
        </button>
      </div>

      {/* ── Center: Search ─────────────────────────────────────── */}
      <div className="flex-1 max-w-[340px] mx-auto">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-600 pointer-events-none" />
          <input
            type="text"
            placeholder={t.header.search}
            readOnly
            className="w-full bg-neutral-900 border border-neutral-800 rounded-lg pl-9 pr-14 py-[7px] text-[12px] text-neutral-400 placeholder-neutral-600 focus:outline-none cursor-default"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[9px] text-neutral-600 bg-neutral-800 border border-neutral-700 px-1.5 py-0.5 rounded font-mono">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* ── Right: Sync time + actions ─────────────────────────── */}
      <div className="flex items-center gap-3 flex-shrink-0 ml-auto">
        <div className="text-right">
          <div className="text-[9px] text-neutral-600 tracking-[0.12em]">{t.header.lastSync}</div>
          <div className="text-[11px] font-mono text-neutral-300 leading-tight">{dateStr}</div>
        </div>
        <button className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800 transition-colors">
          <Bell className="w-4 h-4" />
        </button>
        <button
          onClick={() => window.location.reload()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 rounded-lg text-[12px] text-white transition-colors border border-neutral-700"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{t.header.refresh}</span>
        </button>
      </div>
    </header>
  );
}
