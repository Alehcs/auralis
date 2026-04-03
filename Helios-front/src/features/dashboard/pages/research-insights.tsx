import {
  LineChart,
  BarChart2,
  ScatterChart,
  AlertTriangle,
} from 'lucide-react';
import { GlobalMetrics } from '../components/global-metrics';
import { KFoldResults } from '../components/kfold-results';
import { ArchitectureComparison } from '../components/architecture-comparison';
import { XAIFaithfulness } from '../components/xai-faithfulness';
import { ExperimentLog } from '../components/experiment-log';

interface PlaceholderCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
  status?: 'planned' | 'in-progress';
}

function PlaceholderCard({ icon: Icon, title, description, status = 'planned' }: PlaceholderCardProps) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 p-5 flex flex-col gap-3 hover:border-neutral-700 transition-colors">
      <div className="flex items-start justify-between">
        <div className="w-8 h-8 bg-neutral-800 border border-neutral-700 flex items-center justify-center">
          <Icon className="w-4 h-4 text-neutral-400" />
        </div>
        <span
          className={`text-[10px] font-mono px-2 py-0.5 border ${
            status === 'in-progress'
              ? 'text-blue-400 border-blue-500/30 bg-blue-500/10'
              : 'text-neutral-500 border-neutral-700 bg-neutral-800'
          }`}
        >
          {status === 'in-progress' ? 'IN PROGRESS' : 'PLANNED'}
        </span>
      </div>

      <div>
        <h3 className="text-sm font-medium text-white mb-1">{title}</h3>
        <p className="text-[11px] text-neutral-500 leading-relaxed">{description}</p>
      </div>

      <div className="mt-auto pt-3 border-t border-neutral-800">
        <div className="h-1 bg-neutral-800 w-full">
          <div className={`h-full ${status === 'in-progress' ? 'w-2/5 bg-blue-500' : 'w-0'}`} />
        </div>
      </div>
    </div>
  );
}

const PLANNED_MODULES: PlaceholderCardProps[] = [
  {
    icon: LineChart,
    title: 'Curvas de Validación',
    description: 'Evolución de loss y MAE durante el entrenamiento. Detección de overfitting y convergencia del modelo SolarNet.',
    status: 'in-progress',
  },
  {
    icon: BarChart2,
    title: 'Distribución de Errores',
    description: 'Histograma de residuales entre valores predichos y reales del índice de manchas solares por ciclo solar.',
  },
  {
    icon: ScatterChart,
    title: 'Predicción vs. Realidad',
    description: 'Diagrama de dispersión comparando las predicciones del modelo contra los valores observados del índice SSN.',
  },
  {
    icon: AlertTriangle,
    title: 'Análisis de Casos Extremos',
    description: 'Identificación de magnetogramas con mayor error de predicción y correlación con eventos de alta actividad solar.',
  },
];

export function ResearchInsights() {
  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="bg-neutral-950 border border-neutral-800">
        <div className="border-b border-neutral-800 px-5 py-4 bg-neutral-900">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <LineChart className="w-4 h-4 text-neutral-400" />
                <h2 className="text-sm font-semibold text-white tracking-tight">Research Insights</h2>
              </div>
              <p className="text-[11px] text-neutral-500">
                Validación Científica y Métricas de Rendimiento del Modelo
              </p>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span className="text-[10px] text-neutral-500 font-mono">SolarNet V2 PRO</span>
            </div>
          </div>
        </div>

        <div className="px-5 py-2.5 flex items-center gap-4">
          <span className="text-[11px] text-neutral-500">
            <span className="text-neutral-300 font-mono">5</span> componentes activos
          </span>
          <span className="text-neutral-700">·</span>
          <span className="text-[11px] text-neutral-500">
            <span className="text-blue-400 font-mono">1</span> en progreso
          </span>
          <span className="text-neutral-700">·</span>
          <span className="text-[11px] text-neutral-500">
            <span className="text-neutral-400 font-mono">3</span> planificados
          </span>
        </div>
      </div>

      {/* Live components */}
      <GlobalMetrics />
      <KFoldResults />
      <ArchitectureComparison />
      <XAIFaithfulness />
      <ExperimentLog />

      {/* Planned modules grid */}
      <div className="bg-neutral-950 border border-neutral-800">
        <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
          <h3 className="text-sm font-semibold text-white">Módulos de Análisis</h3>
          <p className="text-[11px] text-neutral-500 mt-0.5">Visualizaciones en desarrollo y planificadas</p>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {PLANNED_MODULES.map((module) => (
              <PlaceholderCard key={module.title} {...module} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
