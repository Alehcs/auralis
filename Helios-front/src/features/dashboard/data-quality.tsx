import { useLanguage } from '@/lib/i18n/language-context';

export function DataQuality() {
  const { t } = useLanguage();

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <h2 className="text-sm font-semibold text-white">{t.dataQuality.title}</h2>
        <p className="text-[11px] text-neutral-500 mt-0.5">{t.dataQuality.subtitle}</p>
      </div>

      <div className="p-4 grid grid-cols-4 gap-4">
        <div className="bg-neutral-900 border border-neutral-800 p-3">
          <div className="text-[11px] text-neutral-500 mb-2">{t.dataQuality.dataLatency}</div>
          <div className="flex items-baseline space-x-2 mb-1">
            <span className="text-2xl font-mono text-white">3.2</span>
            <span className="text-xs text-neutral-500 font-mono">min</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span className="text-[10px] text-neutral-500">{t.dataQuality.normal}</span>
          </div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 p-3">
          <div className="text-[11px] text-neutral-500 mb-2">{t.dataQuality.lastUpdate}</div>
          <div className="flex items-baseline space-x-2 mb-1">
            <span className="text-2xl font-mono text-white">2</span>
            <span className="text-xs text-neutral-500 font-mono">{t.dataQuality.minAgo}</span>
          </div>
          <div className="text-[10px] text-neutral-600 font-mono">14:23:42 UTC</div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 p-3">
          <div className="text-[11px] text-neutral-500 mb-2">{t.dataQuality.completeness}</div>
          <div className="flex items-baseline space-x-2 mb-1">
            <span className="text-2xl font-mono text-white">99.8</span>
            <span className="text-xs text-neutral-500 font-mono">%</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span className="text-[10px] text-neutral-500">{t.dataQuality.excellent}</span>
          </div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 p-3">
          <div className="text-[11px] text-neutral-500 mb-2">{t.dataQuality.missingCadence}</div>
          <div className="flex items-baseline space-x-2 mb-1">
            <span className="text-2xl font-mono text-white">2</span>
            <span className="text-xs text-neutral-500 font-mono">{t.dataQuality.frames}</span>
          </div>
          <div className="text-[10px] text-neutral-600 font-mono">{t.dataQuality.last24h}</div>
        </div>
      </div>

      <div className="px-4 pb-4">
        <div className="bg-neutral-900 border border-neutral-800 p-3">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-[11px] text-neutral-500 mb-3">{t.dataQuality.dataSource}</div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.instrument}:</span>
                  <span className="text-white">SDO/HMI</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.observable}:</span>
                  <span className="text-white">{t.dataQuality.continuumIntensity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.wavelength}:</span>
                  <span className="text-white">6173 Å</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.cadence}:</span>
                  <span className="text-white">45s</span>
                </div>
              </div>
            </div>
            <div>
              <div className="text-[11px] text-neutral-500 mb-3">{t.dataQuality.dataProperties}</div>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.resolution}:</span>
                  <span className="text-white">4096×4096</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.pixelScale}:</span>
                  <span className="text-white">0.5 arcsec</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.dataLevel}:</span>
                  <span className="text-white">1.5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">{t.dataQuality.processing}:</span>
                  <span className="text-white">{t.dataQuality.jsocPipeline}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
