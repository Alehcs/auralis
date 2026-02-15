import { useState, useEffect } from 'react';
import { ChevronDown, Loader2, Eye } from 'lucide-react';
import { getImageList, getImageUrl, predict } from '@/lib/api';
import type { ImageListItem, PredictionResult } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

const API_BASE = 'http://localhost:8000';

export function MagnetogramPanel() {
  const { t } = useLanguage();
  const [images, setImages] = useState<ImageListItem[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gradcamEnabled, setGradcamEnabled] = useState(false);

  // Fetch image list on mount
  useEffect(() => {
    getImageList()
      .then((res) => {
        setImages(res.images);
        if (res.images.length > 0) {
          setSelected(res.images[0].filename);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  // Run prediction whenever selection changes
  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setPrediction(null);
    predict(selected)
      .then((res) => setPrediction(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selected]);

  const riskColor: Record<string, string> = {
    Low: 'bg-green-950 text-green-400 border-green-900',
    Medium: 'bg-yellow-950 text-yellow-400 border-yellow-900',
    High: 'bg-red-950 text-red-400 border-red-900',
  };

  const getRiskLabel = (level: string) => {
    if (level === 'Low') return t.magnetogram.lowRisk;
    if (level === 'Medium') return t.magnetogram.mediumRisk;
    if (level === 'High') return t.magnetogram.highRisk;
    return level.toUpperCase() + ' RISK';
  };

  // Determine image URL based on Grad-CAM toggle
  const imageUrl = gradcamEnabled
    ? `${API_BASE}/api/explain/${selected}`
    : getImageUrl(selected);

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      {/* Header */}
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">{t.magnetogram.title}</h2>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              {t.magnetogram.subtitle}
            </p>
          </div>
          <div className="flex items-center space-x-2 text-[11px]">
            <span className="text-neutral-500">{t.magnetogram.images}:</span>
            <span className="font-mono text-white">{images.length}</span>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Image Selector */}
        <div className="relative">
          <label className="block text-[11px] text-neutral-500 mb-1.5">{t.magnetogram.selectMagnetogram}</label>
          <div className="relative">
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="w-full bg-neutral-900 border border-neutral-700 text-white text-xs font-mono px-3 py-2 pr-8 appearance-none focus:outline-none focus:border-blue-500 transition-colors"
            >
              {images.map((img) => (
                <option key={img.filename} value={img.filename}>
                  {img.date ? `${img.date}  —  ` : ''}{img.filename}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-500 pointer-events-none" />
          </div>
        </div>

        {error && (
          <div className="bg-red-950 border border-red-900 px-3 py-2 text-xs text-red-400">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {/* Magnetogram Image */}
          <div className="bg-neutral-900 border border-neutral-800 p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-[11px] text-neutral-500">
                {gradcamEnabled ? t.magnetogram.gradcamHeatmap : t.magnetogram.renderedMagnetogram}
              </div>
            </div>

            {/* Grad-CAM Toggle */}
            <div className="mb-3 flex items-center justify-between bg-neutral-950 border border-neutral-800 px-3 py-2">
              <div className="flex items-center space-x-2">
                <Eye className={`w-3.5 h-3.5 ${gradcamEnabled ? 'text-blue-400' : 'text-neutral-500'}`} />
                <span className="text-xs text-white">{t.magnetogram.aiVision}</span>
              </div>
              <button
                onClick={() => setGradcamEnabled(!gradcamEnabled)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-neutral-950 ${gradcamEnabled ? 'bg-blue-600' : 'bg-neutral-700'
                  }`}
                role="switch"
                aria-checked={gradcamEnabled}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${gradcamEnabled ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                />
              </button>
            </div>

            {gradcamEnabled && (
              <div className="mb-2 bg-blue-950 border border-blue-900 px-2 py-1.5 text-[10px] text-blue-400">
                {t.magnetogram.gradcamTooltip}
              </div>
            )}

            <div className="relative aspect-square bg-black border border-neutral-800 overflow-hidden">
              {selected ? (
                <img
                  key={imageUrl}
                  src={imageUrl}
                  alt={gradcamEnabled ? 'Grad-CAM Heatmap' : 'SDO/HMI Magnetogram'}
                  className="w-full h-full object-contain transition-opacity duration-300"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-neutral-600 text-xs">
                  {t.magnetogram.noImageSelected}
                </div>
              )}
              <div className="absolute bottom-2 right-2 bg-black/80 px-2 py-1 text-[9px] text-neutral-400 font-mono border border-neutral-700">
                512x512 px
              </div>
            </div>

            {/* Magnetogram Legend */}
            <div className="mt-3 space-y-2">
              {/* Section 1: Physics Interpretation (Always visible) */}
              <div className="bg-neutral-950 border border-neutral-800 px-3 py-2">
                <div className="text-[11px] text-neutral-400 mb-2 font-medium">
                  {t.magnetogram.dataInterpretation}
                </div>
                <div className="space-y-1.5">
                  {/* RdBu_r gradient bar */}
                  <div
                    className="h-3 w-full border border-neutral-700"
                    style={{
                      background: 'linear-gradient(to right, #0000ff, #4040ff, #8080ff, #c0c0c0, #ff8080, #ff4040, #ff0000)',
                    }}
                  />
                  <div className="grid grid-cols-3 text-[9px] text-neutral-500">
                    <div className="text-left">{t.magnetogram.bluePolarity}</div>
                    <div className="text-center">{t.magnetogram.neutral}</div>
                    <div className="text-right">{t.magnetogram.redPolarity}</div>
                  </div>
                </div>
              </div>

              {/* Section 2: AI Interpretation (Only when Grad-CAM enabled) */}
              {gradcamEnabled && (
                <div className="bg-blue-950/30 border border-blue-900/50 px-3 py-2">
                  <div className="text-[11px] text-blue-400 mb-2 font-medium">
                    {t.magnetogram.modelAttention}
                  </div>
                  <div className="space-y-1.5">
                    {/* Inferno gradient bar */}
                    <div
                      className="h-3 w-full border border-blue-900/50"
                      style={{
                        background: 'linear-gradient(to right, #000004, #1b0c41, #4a0c6b, #781c6d, #a52c60, #cf4446, #ed6925, #fb9b06, #f7d13d, #fcffa4)',
                      }}
                    />
                    <div className="text-[9px] text-blue-400/80">
                      {t.magnetogram.gradcamDescription}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Prediction Results */}
          <div className="bg-neutral-900 border border-neutral-800 p-3">
            <div className="text-[11px] text-neutral-500 mb-2">{t.magnetogram.prediction}</div>
            <div className="aspect-square bg-black border border-neutral-800 flex flex-col items-center justify-center p-6">
              {loading ? (
                <div className="flex flex-col items-center space-y-3">
                  <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                  <span className="text-xs text-neutral-500">{t.magnetogram.runningInference}</span>
                </div>
              ) : prediction ? (
                <div className="w-full space-y-6">
                  {/* Sunspot Index */}
                  <div className="text-center">
                    <div className="text-[11px] text-neutral-500 mb-1">{t.magnetogram.sunspotIndex}</div>
                    <div className="text-5xl font-mono text-white font-bold">
                      {prediction.sunspot_index.toFixed(2)}
                    </div>
                    <div className="text-[10px] text-neutral-600 font-mono mt-1">%</div>
                  </div>

                  {/* Risk Level */}
                  <div className="flex justify-center">
                    <span className={`text-sm font-mono px-3 py-1 border ${riskColor[prediction.risk_level] || ''}`}>
                      {getRiskLabel(prediction.risk_level)}
                    </span>
                  </div>

                  {/* Confidence */}
                  <div className="text-center">
                    <div className="text-[11px] text-neutral-500 mb-1">{t.magnetogram.confidence}</div>
                    <div className="text-lg font-mono text-white">
                      {(prediction.confidence * 100).toFixed(1)}%
                    </div>
                  </div>

                  {/* Model info */}
                  <div className="grid grid-cols-2 gap-x-4 text-[11px] font-mono border-t border-neutral-800 pt-3 mt-3">
                    <div className="flex justify-between">
                      <span className="text-neutral-500">{t.magnetogram.model}:</span>
                      <span className="text-white">SolarNet V2</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-500">{t.magnetogram.weights}:</span>
                      <span className="text-white">helios_v2_pro</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-neutral-600">{t.magnetogram.selectImageToPredict}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
