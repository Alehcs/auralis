import { lazy, Suspense, useState } from 'react';
import { ScientificSidebar, type TabId } from './scientific-sidebar';
import { ScientificHeader } from './scientific-header';
import { MagnetogramPanel } from './magnetogram-panel';
import { ModelMetrics } from './model-metrics';
import { ExecutionLogs } from './execution-logs';
import { PredictionChart } from './prediction-chart';
import { ConfigPanel } from './components/config-panel';
import { ResearchInsights } from './pages/research-insights';
import { useLanguage } from '@/lib/i18n/language-context';
import { AgentLabPage } from './agent-lab/AgentLabPage';
import { IS_FROZEN_DEMO } from '@/lib/frozen-demo';

// The isolated viewer exists only while the Simulation tab is mounted.
const SolarTwinPanel = lazy(() =>
  import('./simulation/SolarTwinPanel').then((m) => ({ default: m.SolarTwinPanel })),
);

function SimulationFallback() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl h-[480px] animate-pulse" />
  );
}

/**
 * Main dashboard shell.
 *
 * The dashboard is intentionally tab-driven instead of route-driven because the
 * demo is a single analytical workspace: switching tabs should preserve the
 * surrounding scientific header/sidebar context while each panel owns its own
 * data loading lifecycle.
 */
export function DashboardPage() {
  const { language } = useLanguage();
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
            {activeTab === 'simulation'  && (
              <Suspense fallback={<SimulationFallback />}>
                <SolarTwinPanel />
              </Suspense>
            )}
            {activeTab !== 'simulation' && activeTab !== 'agentlab' && (
              <details className="mt-5 border-t border-neutral-800 text-sm text-neutral-400">
                <summary className="cursor-pointer py-3 hover:text-neutral-200">
                  {language === 'es' ? 'Sobre los datos' : 'About the data'}
                </summary>
                <div className="space-y-2 pb-3 leading-relaxed">
                  {IS_FROZEN_DEMO && <p>{language === 'es'
                    ? 'Resultados guardados. Sin nuevas inferencias ni análisis de archivos.'
                    : 'Saved results. New inference and file analysis are unavailable.'}</p>}
                  <p>{language === 'es'
                    ? 'V3.1: 263 observaciones de validación usadas para seleccionar el modelo; no son un test independiente ni temporal. MAE: MC Dropout 0,10156; API determinista 0,20408 puntos SI. El benchmark V3 histórico tiene fuga de datos y se presenta por separado.'
                    : 'V3.1: 263 validation observations used for model selection, not an independent or temporal test. MAE: MC Dropout 0.10156; deterministic API 0.20408 SI points. The historical V3 benchmark has data leakage and is shown separately.'}</p>
                  <p>{language === 'es'
                    ? 'SI: porcentaje de píxeles originales con |B LOS| > 200 G. C/M/X son bandas internas, no clases GOES. La confianza y la dispersión por ruido son heurísticas.'
                    : 'SI: percentage of original pixels with |B LOS| > 200 G. C/M/X are internal bands, not GOES classes. Confidence and noise spread are heuristic.'}</p>
                </div>
              </details>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
