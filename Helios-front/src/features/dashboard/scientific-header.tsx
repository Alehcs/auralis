import { RefreshCw } from 'lucide-react';

export function ScientificHeader() {
  const currentTime = new Date().toISOString().split('.')[0] + 'Z';
  
  return (
    <div className="border-b border-neutral-800 bg-neutral-950 px-6 py-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white mb-0.5">Solar Activity Prediction Dashboard</h1>
          <div className="flex items-center space-x-4 text-xs text-neutral-400">
            <span>HeliosPipeline</span>
            <span>•</span>
            <span>SDO/HMI Magnetogram Analysis</span>
            <span>•</span>
            <span className="font-mono">{currentTime}</span>
          </div>
        </div>
        <button className="flex items-center space-x-2 px-3 py-1.5 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-white text-xs transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
}
