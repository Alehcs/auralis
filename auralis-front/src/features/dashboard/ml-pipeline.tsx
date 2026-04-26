import { Database, Cpu, Brain, BarChart3, ArrowRight } from 'lucide-react';

export function MLPipeline() {
  const stages = [
    {
      icon: Database,
      title: 'Data Ingestion',
      description: 'NASA SDO/HMI',
      status: 'active',
      color: 'blue'
    },
    {
      icon: Cpu,
      title: 'Preprocessing',
      description: 'Image Pipeline',
      status: 'active',
      color: 'purple'
    },
    {
      icon: Brain,
      title: 'CNN Model',
      description: 'Detection & Prediction',
      status: 'active',
      color: 'orange'
    },
    {
      icon: BarChart3,
      title: 'Dashboard',
      description: 'Real-time Viz',
      status: 'active',
      color: 'green'
    }
  ];

  return (
    <div className="bg-black/40 border border-white/10 rounded-xl p-6 mb-6">
      <h2 className="text-xl font-bold text-white mb-6">ML Pipeline Architecture</h2>
      
      <div className="flex items-center justify-between">
        {stages.map((stage, index) => {
          const Icon = stage.icon;
          const colorClasses = {
            blue: 'from-blue-500 to-blue-600 border-blue-500/30',
            purple: 'from-purple-500 to-purple-600 border-purple-500/30',
            orange: 'from-orange-500 to-orange-600 border-orange-500/30',
            green: 'from-green-500 to-green-600 border-green-500/30'
          };

          return (
            <div key={stage.title} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={`w-20 h-20 rounded-xl bg-gradient-to-br ${colorClasses[stage.color as keyof typeof colorClasses]} border flex items-center justify-center mb-3 relative`}>
                  <Icon className="w-10 h-10 text-white" />
                  {stage.status === 'active' && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                  )}
                </div>
                <h3 className="text-sm font-semibold text-white text-center mb-1">{stage.title}</h3>
                <p className="text-xs text-gray-400 text-center">{stage.description}</p>
              </div>
              
              {index < stages.length - 1 && (
                <div className="flex items-center mx-4 mb-12">
                  <div className="w-16 h-0.5 bg-gradient-to-r from-white/30 to-white/10" />
                  <ArrowRight className="w-5 h-5 text-white/30 -ml-1" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-8 grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">Pipeline Uptime</p>
          <p className="text-2xl font-bold text-white">99.8%</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">Avg Latency</p>
          <p className="text-2xl font-bold text-white">2.4s</p>
        </div>
        <div className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 border border-orange-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">Daily Predictions</p>
          <p className="text-2xl font-bold text-white">1,247</p>
        </div>
      </div>
    </div>
  );
}
