import { Database, Cpu, Brain, LineChart, ArrowRight } from 'lucide-react';

export function ArchitectureDiagram() {
  const stages = [
    {
      icon: Database,
      label: 'Data Ingestion',
      detail: 'SDO/HMI Stream'
    },
    {
      icon: Cpu,
      label: 'Preprocessing',
      detail: 'Image Pipeline'
    },
    {
      icon: Brain,
      label: 'CNN Model',
      detail: 'Detection'
    },
    {
      icon: LineChart,
      label: 'Inference',
      detail: 'Current Index'
    }
  ];

  return (
    <div className="px-6 py-16 bg-neutral-900">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-semibold text-white mb-2">Pipeline Architecture</h2>
          <p className="text-sm text-neutral-500">End-to-end ML workflow</p>
        </div>

        <div className="flex items-center justify-between">
          {stages.map((stage, index) => {
            const Icon = stage.icon;
            return (
              <div key={stage.label} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-neutral-950 border border-neutral-700 flex items-center justify-center mb-3">
                    <Icon className="w-8 h-8 text-neutral-400" />
                  </div>
                  <div className="text-sm font-medium text-white mb-1">{stage.label}</div>
                  <div className="text-xs text-neutral-500">{stage.detail}</div>
                </div>
                
                {index < stages.length - 1 && (
                  <div className="flex items-center mx-6 mb-8">
                    <div className="w-12 h-px bg-neutral-700" />
                    <ArrowRight className="w-4 h-4 text-neutral-700 -ml-1" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-12 bg-neutral-950 border border-neutral-800 p-6">
          <div className="grid grid-cols-3 gap-6 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-neutral-500">ONNX Inference:</span>
              <span className="text-white">25.11 ms · CPU</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Model Size:</span>
              <span className="text-white">86.6 KB · ONNX</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">MAE (log-SI):</span>
              <span className="text-white">0.1048</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
