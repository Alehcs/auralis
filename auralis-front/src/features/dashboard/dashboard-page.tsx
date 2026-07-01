import { useState } from 'react';
import { ScientificSidebar, type TabId } from './scientific-sidebar';
import { ScientificHeader } from './scientific-header';
import { MagnetogramPanel } from './magnetogram-panel';
import { ModelMetrics } from './model-metrics';
import { ExecutionLogs } from './execution-logs';
import { PredictionChart } from './prediction-chart';
import { ConfigPanel } from './components/config-panel';
import { ResearchInsights } from './pages/research-insights';
import { AgentLabPage } from './agent-lab/AgentLabPage';
import { SolarSimulationPage } from './simulation/SolarSimulationPage';

/**
 * Main dashboard shell.
 *
 * The dashboard is intentionally tab-driven instead of route-driven because the
 * demo is a single analytical workspace: switching tabs should preserve the
 * surrounding scientific header/sidebar context while each panel owns its own
 * data loading lifecycle.
 */
export function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    setSidebarOpen(false);
  };

  return (
    <div className="h-screen overflow-hidden bg-[#0d0d0d] flex">

      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <ScientificSidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
        <ScientificHeader onMenuClick={() => setSidebarOpen(true)} />

        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 md:p-5">
          <div className="max-w-[1600px] mx-auto">
            {activeTab === 'overview'    && <ModelMetrics />}
            {activeTab === 'monitoring'  && <MagnetogramPanel />}
            {activeTab === 'pipeline'    && <PredictionChart />}
            {activeTab === 'logs'        && <ExecutionLogs />}
            {activeTab === 'config'      && <ConfigPanel />}
            {activeTab === 'research'    && <ResearchInsights />}
            {activeTab === 'agentlab'    && <AgentLabPage />}
            {activeTab === 'simulation'  && <SolarSimulationPage />}
          </div>
        </div>
      </main>
    </div>
  );
}
