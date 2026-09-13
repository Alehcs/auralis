import { CheckCircle } from 'lucide-react';

export function ProjectDescription() {
  const useCases = [
    'Space weather research and monitoring',
    'Solar activity index estimation',
    'Machine-learning engineering portfolio demonstration',
    'Data pipeline and MLOps case study'
  ];

  const technicalFeatures = [
    { label: 'Dataset Size', value: '1,314 unique / 1,763 rows' },
    { label: 'V3.1 MC MAPE (selection validation)', value: '5.9870%' },
    { label: 'V3.1 MC MAE (SI percentage points)', value: '0.10156' },
    { label: 'V3.1 deterministic API MAE (SI pp)', value: '0.20408' },
    { label: 'Synthetic noise sensitivity', value: '20-pass ONNX' },
    { label: 'SDO/HMI Cadence', value: '45 s' }
  ];

  return (
    <div className="px-6 py-16 bg-neutral-950">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-semibold text-white mb-2">About the Project</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Description */}
          <div className="space-y-4">
            <p className="text-sm text-neutral-300 leading-relaxed">
              Auralis is an end-to-end machine learning and data engineering system for estimating solar activity from NASA SDO/HMI magnetograms.
            </p>
            <p className="text-sm text-neutral-300 leading-relaxed">
              The platform processes local solar imagery, identifies active magnetic regions with computer vision, and reports the current activity index with an illustrative sensitivity diagnostic. Historical validation contains repeated observations across train and validation; retraining is required.
            </p>
            
            <div className="pt-4">
              <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-3">Use Cases</h3>
              <div className="space-y-2">
                {useCases.map((useCase) => (
                  <div key={useCase} className="flex items-start space-x-2">
                    <CheckCircle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-neutral-400">{useCase}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Technical Features */}
          <div>
            <div className="bg-neutral-900 border border-neutral-800 p-6">
              <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-4">
                Key Metrics
              </h3>
              <div className="space-y-4">
                {technicalFeatures.map((feature) => (
                  <div key={feature.label} className="flex items-center justify-between pb-4 border-b border-neutral-800 last:border-0 last:pb-0">
                    <span className="text-sm text-neutral-400">{feature.label}</span>
                    <span className="text-lg font-mono text-white">{feature.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 bg-neutral-900 border border-neutral-800 p-6">
              <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-4">
                Technology Stack
              </h3>
              <div className="flex flex-wrap gap-2">
                {['Python', 'PyTorch', 'ONNX Runtime', 'FastAPI', 'NumPy / SciPy', 'Coronium V3.1', 'Grad-CAM', 'React', 'Recharts'].map((tech) => (
                  <span key={tech} className="px-2 py-1 bg-neutral-950 border border-neutral-700 text-xs text-neutral-300 font-mono">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
