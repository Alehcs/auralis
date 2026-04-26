import { useState, useEffect } from 'react';
import {
  Sun, LayoutDashboard, Activity,
  Database, FlaskConical, FileText, Settings,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/language-context';

export type TabId = 'overview' | 'monitoring' | 'pipeline' | 'logs' | 'config' | 'research';

interface ScientificSidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function ScientificSidebar({ activeTab, onTabChange, isOpen, onClose }: ScientificSidebarProps) {
  const { t } = useLanguage();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const tickStr = now.toLocaleTimeString('en-GB', { hour12: false });

  const NAV_ITEMS: { icon: typeof LayoutDashboard; label: string; id: TabId }[] = [
    { icon: LayoutDashboard, label: t.nav.dashboard,    id: 'overview'   },
    { icon: Activity,        label: t.nav.monitoring,   id: 'monitoring' },
    { icon: Database,        label: t.nav.pipeline,     id: 'pipeline'   },
    { icon: FlaskConical,    label: t.nav.experiments,  id: 'research'   },
    { icon: FileText,        label: t.nav.logs,         id: 'logs'       },
    { icon: Settings,        label: t.nav.settings,     id: 'config'     },
  ];

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-50 w-[220px] flex-shrink-0
        bg-[#0d0d0d] border-r border-neutral-800/60 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:relative md:translate-x-0 md:z-auto
      `}
    >
      {/* ── Logo ─────────────────────────────────────────────────── */}
      <div className="px-5 py-5 flex items-center gap-3.5">
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"
          style={{ background: 'linear-gradient(135deg, #fb923c 0%, #f97316 40%, #ea580c 100%)' }}
        >
          <Sun className="w-5 h-5 text-black" strokeWidth={2.2} />
        </div>
        <div className="leading-none">
          <div className="text-[17px] font-bold text-white tracking-tight">Auralis</div>
          <div className="text-[10px] text-neutral-400 tracking-[0.2em] mt-1">SOLAR INTELLIGENCE</div>
        </div>
      </div>

      {/* ── Nav ──────────────────────────────────────────────────── */}
      <div className="px-3 flex-1">
        <div className="text-[9px] text-neutral-600 tracking-[0.18em] px-2.5 mb-2">
          {t.nav.workspace}
        </div>
        <nav className="space-y-[2px]">
          {NAV_ITEMS.map(({ icon: Icon, label, id }) => {
            const active = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => { onTabChange(id); onClose(); }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-[14px] transition-colors ${
                  active
                    ? 'bg-neutral-800/80 text-white'
                    : 'text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-[17px] h-[17px] flex-shrink-0 ${active ? 'text-neutral-300' : 'text-neutral-600'}`} />
                  <span>{label}</span>
                </div>
                {active && <div className="w-[6px] h-[6px] rounded-full bg-orange-500 flex-shrink-0" />}
              </button>
            );
          })}
        </nav>
      </div>

      {/* ── Status bar ───────────────────────────────────────────── */}
      <div className="px-4 py-4 border-t border-neutral-800/60">
        <div className="flex items-center gap-2">
          <div className="w-[7px] h-[7px] rounded-full bg-green-500 flex-shrink-0" />
          <span className="text-[12px] text-neutral-300">{t.nav.pipelineOnline}</span>
        </div>
        <div className="text-[10px] text-neutral-600 font-mono mt-1 pl-[15px]">
          {t.nav.lastTick} {tickStr} · CPU
        </div>
      </div>
    </aside>
  );
}
