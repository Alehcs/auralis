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
            {IS_FROZEN_DEMO && <p role="note" className="mb-4 rounded-lg border border-amber-700/40 bg-amber-950/20 px-4 py-3 text-sm text-amber-200">
              Demo con resultados guardados · sin backend activo, nuevas inferencias ni subida de archivos. Las fechas y métricas corresponden a los archivos originales; Simulación conserva sus cinco estados HMI y acceso AR.
            </p>}
            {activeTab !== 'simulation' && activeTab !== 'agentlab' && (
              <p className="mb-4 text-xs text-amber-300" role="note">
                {language === 'es'
                  ? 'V3.1 activo: validación limpia de 263 observaciones usada para selección, no test independiente ni temporal. MAE MC Dropout: 0,10156; API determinista: 0,20408 puntos SI. Benchmark V3 histórico con fuga, separado. SI = % de píxeles originales con |B LOS| > 200 G. C/M/X son bandas internas, no clases GOES; confianza y dispersión por ruido son heurísticas.'
                  : 'V3.1 active: 263 clean validation observations used for selection, not an independent or temporal test. MC Dropout MAE: 0.10156; deterministic API: 0.20408 SI points. Historical V3 benchmark has leakage and remains separate. SI = % of original pixels with |B LOS| > 200 G. C/M/X are internal bands, not GOES classes; confidence and noise spread are heuristic.'}
              </p>
            )}
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
          </div>
        </div>
      </main>
    </div>
  );
}
