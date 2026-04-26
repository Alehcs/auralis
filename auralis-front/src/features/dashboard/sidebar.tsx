import { LayoutDashboard, Activity, Database, Settings, Telescope, TrendingUp } from 'lucide-react';

export function Sidebar() {
  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', active: true },
    { icon: Activity, label: 'Live Monitoring', active: false },
    { icon: TrendingUp, label: 'Predictions', active: false },
    { icon: Telescope, label: 'Magnetograms', active: false },
    { icon: Database, label: 'Data Pipeline', active: false },
    { icon: Settings, label: 'Settings', active: false },
  ];

  return (
    <aside className="w-64 bg-black/40 border-r border-white/10 flex flex-col">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center">
            <Telescope className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white">Auralis</h1>
            <p className="text-xs text-gray-400">v3.0.0</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                item.active 
                  ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs text-gray-400">System Status</span>
          </div>
          <p className="text-sm text-white">All systems operational</p>
        </div>
      </div>
    </aside>
  );
}
