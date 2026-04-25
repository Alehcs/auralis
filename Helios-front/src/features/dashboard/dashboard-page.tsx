import { useState } from 'react';
import { ScientificSidebar, type TabId } from './scientific-sidebar';
import { ScientificHeader } from './scientific-header';
import { MagnetogramPanel } from './magnetogram-panel';
import { ModelMetrics } from './model-metrics';
import { ExecutionLogs } from './execution-logs';
import { PredictionChart } from './prediction-chart';
import { ConfigPanel } from './components/config-panel';
import { ResearchInsights } from './pages/research-insights';

export function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex">
      <ScientificSidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 flex flex-col min-w-0">
        <ScientificHeader />

        <div className="flex-1 overflow-y-auto p-5">
          <div className="max-w-[1600px] mx-auto">
            {activeTab === 'overview'    && <ModelMetrics />}
            {activeTab === 'monitoring'  && <MagnetogramPanel />}
            {activeTab === 'pipeline'    && <PredictionChart />}
            {activeTab === 'logs'        && <ExecutionLogs />}
            {activeTab === 'config'      && <ConfigPanel />}
            {activeTab === 'research'    && <ResearchInsights />}
          </div>
        </div>
      </main>
    </div>
  );
}
