import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { getStats } from '@/lib/api';
import type { SystemStats } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

export function ModelMetrics() {
  const { t } = useLanguage();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats()
      .then((data) => setStats(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-neutral-950 border border-neutral-800 p-8 flex items-center justify-center">
        <Loader2 className="w-5 h-5 text-neutral-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-950 border border-neutral-800 p-4">
        <div className="bg-red-950 border border-red-900 px-3 py-2 text-xs text-red-400">{error}</div>
      </div>
    );
  }

  const metrics = [
    { label: t.metrics.mae, value: stats?.mae.toFixed(4) ?? '--', unit: '%', target: '< 0.50', status: 'pass' },
    { label: t.metrics.totalImages, value: stats?.total_images.toLocaleString() ?? '--', unit: '', target: '> 500', status: 'pass' },
    { label: t.metrics.diskUsage, value: stats?.disk_usage_mb.toFixed(1) ?? '--', unit: 'MB', target: '', status: 'pass' },
  ];

  const trainingInfo = [
    { label: t.metrics.architecture, value: 'SolarNet (4-Conv CNN)' },
    { label: t.metrics.parameters, value: '389,057' },
    { label: t.metrics.inputSize, value: '512 x 512' },
    { label: t.metrics.epochs, value: '26 (early stop)' },
    { label: t.metrics.batchSize, value: '32' },
    { label: t.metrics.learningRate, value: '5e-4 (final)' },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-neutral-950 border border-neutral-800">
        <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
          <h2 className="text-sm font-semibold text-white">{t.metrics.modelPerformance}</h2>
          <p className="text-[11px] text-neutral-500 mt-0.5">{t.metrics.modelPerformanceSubtitle}</p>
        </div>

        <div className="p-4">
          <div className="grid grid-cols-3 gap-3">
            {metrics.map((metric) => (
              <div key={metric.label} className="bg-neutral-900 border border-neutral-800 p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] text-neutral-500">{metric.label}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                </div>
                <div className="flex items-baseline space-x-1">
                  <span className="text-lg font-mono text-white">{metric.value}</span>
                  <span className="text-[10px] text-neutral-500 font-mono">{metric.unit}</span>
                </div>
                {metric.target && (
                  <div className="text-[10px] text-neutral-600 font-mono mt-1">
                    {t.metrics.target}: {metric.target}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-4 bg-neutral-900 border border-neutral-800 p-3">
            <div className="text-[11px] text-neutral-500 mb-3">{t.metrics.trainingConfiguration}</div>
            <div className="grid grid-cols-3 gap-x-6 gap-y-2 text-xs font-mono">
              {trainingInfo.map((info) => (
                <div key={info.label} className="flex justify-between">
                  <span className="text-neutral-400">{info.label}:</span>
                  <span className="text-white">{info.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-neutral-950 border border-neutral-800">
        <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
          <h2 className="text-sm font-semibold text-white">{t.metrics.datasetOverview}</h2>
          <p className="text-[11px] text-neutral-500 mt-0.5">
            {t.metrics.lastUpdated}: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : '--'}
          </p>
        </div>

        <div className="p-4">
          <div className="space-y-3">
            {/* Total Images */}
            <div className="bg-neutral-900 border border-neutral-800 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-white">{t.metrics.processedImages}</span>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                  <span className="text-[10px] font-mono text-green-400">{t.metrics.ready}</span>
                </div>
              </div>
              <div className="text-2xl font-mono text-white">{stats?.total_images.toLocaleString()}</div>
              <div className="text-[10px] text-neutral-600 font-mono mt-1">{t.metrics.npyFiles}</div>
            </div>

            {/* Disk Usage */}
            <div className="bg-neutral-900 border border-neutral-800 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-white">{t.metrics.diskUsage}</span>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                  <span className="text-[10px] font-mono text-blue-400">{t.metrics.nominal}</span>
                </div>
              </div>
              <div className="flex items-baseline space-x-1">
                <span className="text-2xl font-mono text-white">
                  {stats ? (stats.disk_usage_mb / 1024).toFixed(2) : '--'}
                </span>
                <span className="text-xs text-neutral-500 font-mono">{t.metrics.diskUsageUnit}</span>
              </div>
              <div className="text-[10px] text-neutral-600 font-mono mt-1">
                {stats?.disk_usage_mb.toFixed(1)} {t.metrics.diskUsageDetail}
              </div>
            </div>

            {/* Model MAE */}
            <div className="bg-neutral-900 border border-neutral-800 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-white">{t.metrics.bestValidationMAE}</span>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                  <span className="text-[10px] font-mono text-green-400">{t.metrics.optimal}</span>
                </div>
              </div>
              <div className="flex items-baseline space-x-1">
                <span className="text-2xl font-mono text-white">{stats?.mae.toFixed(4)}</span>
                <span className="text-xs text-neutral-500 font-mono">%</span>
              </div>
              <div className="text-[10px] text-neutral-600 font-mono mt-1">{t.metrics.meanAbsoluteError}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
