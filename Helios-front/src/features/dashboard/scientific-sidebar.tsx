import { Activity, Database, FileText, Settings, BarChart3 } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/language-context';

export type TabId = 'overview' | 'monitoring' | 'pipeline' | 'logs' | 'config';

interface ScientificSidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export function ScientificSidebar({ activeTab, onTabChange }: ScientificSidebarProps) {
  const { t } = useLanguage();

  const menuItems: { icon: typeof BarChart3; label: string; id: TabId }[] = [
    { icon: BarChart3, label: t.sidebar.overview, id: 'overview' },
    { icon: Activity, label: t.sidebar.monitoring, id: 'monitoring' },
    { icon: Database, label: t.sidebar.dataPipeline, id: 'pipeline' },
    { icon: FileText, label: t.sidebar.logs, id: 'logs' },
    { icon: Settings, label: t.sidebar.config, id: 'config' },
  ];

  return (
    <aside className="w-56 bg-neutral-950 border-r border-neutral-800 flex flex-col">
      <div className="p-4 border-b border-neutral-800">
        <div className="mb-2">
          <h1 className="text-sm font-semibold text-white tracking-tight">HeliosPipeline</h1>
          <p className="text-[11px] text-neutral-500 font-mono">v2.1.0</p>
        </div>
      </div>

      <nav className="flex-1 p-3">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center space-x-2 px-3 py-2 mb-1 text-sm transition-colors ${activeTab === item.id
                ? 'bg-neutral-800 text-white'
                : 'text-neutral-400 hover:bg-neutral-900 hover:text-neutral-300'
                }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-3 border-t border-neutral-800">
        <div className="bg-neutral-900 border border-neutral-800 p-3">
          <div className="flex items-center space-x-2 mb-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span className="text-[11px] text-neutral-400">{t.sidebar.systemStatus}</span>
          </div>
          <p className="text-xs text-white">{t.sidebar.nominal}</p>
        </div>
      </div>
    </aside>
  );
}
