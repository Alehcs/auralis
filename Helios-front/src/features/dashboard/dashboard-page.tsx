import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '@/lib/i18n/language-context';
import { ScientificSidebar, type TabId } from './scientific-sidebar';
import { ScientificHeader } from './scientific-header';
import { MagnetogramPanel } from './magnetogram-panel';
import { ModelMetrics } from './model-metrics';
import { ExecutionLogs } from './execution-logs';
import { DataQuality } from './data-quality';
import { PredictionChart } from './prediction-chart';
import { ConfigPanel } from './components/config-panel';
import { ResearchInsights } from './pages/research-insights';
import { ArrowLeft } from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const handleBackToLanding = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-neutral-950 flex">
      <ScientificSidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 flex flex-col">
        <ScientificHeader />

        <div className="border-b border-neutral-800 bg-neutral-950 px-6 py-2">
          <button
            onClick={handleBackToLanding}
            className="flex items-center space-x-2 text-xs text-neutral-400 hover:text-neutral-300 transition-colors"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>{t.dashboard.backToOverview}</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-[1920px] mx-auto space-y-4">
            {activeTab === 'overview' && (
              <>
                <ModelMetrics />
                <DataQuality />
              </>
            )}

            {activeTab === 'monitoring' && (
              <>
                <MagnetogramPanel />
              </>
            )}

            {activeTab === 'pipeline' && (
              <>
                <PredictionChart />
              </>
            )}

            {activeTab === 'logs' && (
              <>
                <ExecutionLogs />
              </>
            )}

            {activeTab === 'config' && (
              <ConfigPanel />
            )}

            {activeTab === 'research' && (
              <ResearchInsights />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
