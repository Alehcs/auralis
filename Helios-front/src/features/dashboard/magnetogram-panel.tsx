import { useState, useEffect } from 'react';
import { ChevronDown, Cpu, Eye } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  getImageList, getImageUrl, getAiaUrl, predictDual,
  getExplainPanelsUrl, getPolaritySeries,
} from '@/lib/api';
import type { ImageListItem, PredictionResult } from '@/lib/types';
import type { PolarityPoint } from '@/lib/api';
import { useLanguage } from '@/lib/i18n/language-context';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function flareClass(risk: string) {
  if (risk === 'High') return 'X-class';
  if (risk === 'Medium') return 'M-class';
  return 'B-class';
}

function riskColors(risk: string) {
  if (risk === 'High')
    return { bg: 'bg-red-900/40 border-red-700/50', text: 'text-red-400' };
  if (risk === 'Medium')
    return { bg: 'bg-amber-900/40 border-amber-700/50', text: 'text-amber-400' };
  return { bg: 'bg-green-900/30 border-green-700/40', text: 'text-green-400' };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Badge({ label, color = 'amber' }: { label: string; color?: 'amber' | 'blue' }) {
  const cls = color === 'blue'
    ? 'bg-blue-500/15 border-blue-500/30 text-blue-300'
    : 'bg-amber-500/15 border-amber-500/30 text-amber-300';
  return (
    <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${cls}`}>
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function MagnetogramPanel() {
  const { t } = useLanguage();
  const m = t.monitoring;
  const [images, setImages] = useState<ImageListItem[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [predLoading, setPredLoading] = useState(false);
  const [gradcamOn, setGradcamOn] = useState(false);
  const [panelImgKey, setPanelImgKey] = useState(0);
  const [polarity, setPolarity] = useState<PolarityPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load image list once
  useEffect(() => {
    getImageList()
      .then((res) => {
        setImages(res.images);
        if (res.images.length > 0) setSelected(res.images[0].filename);
      })
      .catch((e) => setError(e.message));

    getPolaritySeries(48)
      .then(setPolarity)
      .catch(console.error);
  }, []);

  // Run inference when selection changes
  useEffect(() => {
    if (!selected) return;
    setPredLoading(true);
    setPrediction(null);
    predictDual(selected)
      .then(setPrediction)
      .catch((e) => setError(e.message))
      .finally(() => setPredLoading(false));
  }, [selected]);

  // Force image reload when selection changes while Grad-CAM is on
  useEffect(() => {
    if (gradcamOn) setPanelImgKey((k) => k + 1);
  }, [selected, gradcamOn]);

  const magnetoUrl = getImageUrl(selected);
  const aiaUrl = getAiaUrl(selected);
  const selectedImg = images.find((i) => i.filename === selected);
  const dateLabel = selectedImg?.date ?? '—';
  const risk = prediction?.risk_level ?? 'Low';
  const { bg, text } = riskColors(risk);
  const confPct = prediction ? prediction.confidence * 100 : 0;

  return (
    <div className="space-y-4">

      {/* ── Image selector ─────────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <span className="text-[11px] text-neutral-500 flex-shrink-0">{m.observation}</span>
        <div className="relative max-w-sm">
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="w-full bg-neutral-900 border border-neutral-800 rounded-lg text-[12px] font-mono text-white px-3 py-1.5 pr-8 appearance-none focus:outline-none focus:border-neutral-600 transition-colors"
          >
            {images.map((img) => (
              <option key={img.filename} value={img.filename}>
                {img.date ? `${img.date}` : img.filename}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-500 pointer-events-none" />
        </div>
        {error && (
          <span className="text-[11px] text-red-400 font-mono">{error}</span>
        )}
      </div>

      {/* ── Top 3-column row ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[1fr_1fr_360px] gap-4">

        {/* ── Magnetogram ──────────────────────────────────────────── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 flex items-center justify-between border-b border-neutral-800">
            <div>
              <div className="text-[14px] font-semibold text-white">{m.magnetogram}</div>
              <div className="text-[11px] text-neutral-500 mt-0.5">
                {m.hmiLos} · {dateLabel} {m.utc}
              </div>
            </div>
            <Badge label="HMI" />
          </div>
          <div className="aspect-square bg-black">
            {selected ? (
              <img
                key={magnetoUrl}
                src={magnetoUrl}
                alt="SDO/HMI Magnetogram"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-neutral-700 text-xs">
                {m.noImage}
              </div>
            )}
          </div>
        </div>

        {/* ── EUV 193Å ─────────────────────────────────────────────── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 flex items-center justify-between border-b border-neutral-800">
            <div>
              <div className="text-[14px] font-semibold text-white">{m.euv}</div>
              <div className="text-[11px] text-neutral-500 mt-0.5">
                {m.coronalPlasma} · {dateLabel} {m.utc}
              </div>
            </div>
            <Badge label="AIA" color="blue" />
          </div>
          <div className="aspect-square bg-black">
            {selected ? (
              <img
                key={aiaUrl}
                src={aiaUrl}
                alt="AIA 193Å EUV"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-neutral-700 text-xs">
                {m.noImage}
              </div>
            )}
          </div>
        </div>

        {/* ── Prediction ───────────────────────────────────────────── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex flex-col gap-4">

          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[14px] font-semibold text-white">{m.prediction}</div>
              <div className="text-[11px] text-neutral-500 mt-0.5">{dateLabel} {m.utc}</div>
            </div>
            <span className="flex items-center gap-1.5 text-[11px] text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              {m.live}
            </span>
          </div>

          {/* Solar Activity Index */}
          <div>
            <div className="text-[9px] text-neutral-500 tracking-[0.15em] mb-1">
              {m.solarActivity}
            </div>
            {predLoading ? (
              <div className="text-[38px] font-mono font-bold text-neutral-600">…</div>
            ) : (
              <div className="text-[38px] font-mono font-bold text-orange-400 leading-none">
                {prediction?.sunspot_index?.toFixed(4) ?? '—'}
              </div>
            )}
            <div className="text-[11px] text-neutral-500 mt-1">
              {m.predictedFlare}{' '}
              <span className="text-cyan-400 font-medium">{flareClass(risk)}</span>
            </div>
          </div>

          {/* Risk + Confidence */}
          <div className="grid grid-cols-2 gap-3">
            <div className={`rounded-lg border p-3 ${bg}`}>
              <div className="text-[9px] text-neutral-500 tracking-[0.14em] mb-1.5">
                {m.riskLevel}
              </div>
              <div className={`text-[20px] font-bold font-mono ${text}`}>
                {risk.toUpperCase()}
              </div>
            </div>
            <div className="rounded-lg border border-neutral-700 bg-neutral-800/50 p-3">
              <div className="text-[9px] text-neutral-500 tracking-[0.14em] mb-1.5">
                {m.confidence}
              </div>
              <div className="text-[20px] font-bold font-mono text-white">
                {prediction ? `${confPct.toFixed(1)}%` : '—'}
              </div>
              {prediction && (
                <div className="mt-2 h-1 bg-neutral-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-orange-500 transition-all duration-700"
                    style={{ width: `${confPct}%` }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Model row */}
          <div className="flex items-center justify-between text-[11px] py-2 border-t border-neutral-800">
            <div className="flex items-center gap-1.5 text-neutral-500">
              <Cpu className="w-3.5 h-3.5" />
              <span>{m.model}</span>
            </div>
            <span className="text-neutral-300 font-mono">SolarNetV3 PRO · v3.0</span>
          </div>

          {/* Grad-CAM toggle */}
          <button
            onClick={() => setGradcamOn(!gradcamOn)}
            className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg border transition-colors ${gradcamOn
                ? 'bg-orange-500/10 border-orange-500/50 text-orange-400'
                : 'bg-neutral-800/60 border-neutral-700 text-neutral-400 hover:text-neutral-300'
              }`}
          >
            <div className="flex items-center gap-2 text-[12px] font-medium">
              <Eye className="w-4 h-4" />
              {m.aiVision}
            </div>
            <span className={`text-[11px] font-mono font-bold ${gradcamOn ? 'text-orange-400' : 'text-neutral-600'}`}>
              {gradcamOn ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>
      </div>

      {/* ── Bottom: Grad-CAM + Polarity chart ──────────────────────── */}
      {gradcamOn && (
        <div className="space-y-4">

          {/* Grad-CAM 3-panel full-width */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-neutral-800 flex items-center justify-between">
              <div>
                <div className="text-[13px] font-semibold text-white">{m.gradcamTitle}</div>
                <div className="text-[11px] text-neutral-500 mt-0.5">
                  {m.gradcamSubtitle} — stage4.conv · K=96
                </div>
              </div>
              <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
                XAI
              </span>
            </div>
            <div className="bg-black p-1">
              <img
                key={`panels-${panelImgKey}-${selected}`}
                src={getExplainPanelsUrl(selected)}
                alt="Grad-CAM 3-panel: B+ | B− | Grad-CAM on |B|"
                className="w-full object-contain"
              />
            </div>
            <div className="px-5 py-2.5 border-t border-neutral-800">
              <p className="text-[10px] text-neutral-600 font-mono">
                L<sub>GC</sub> = ReLU(Σ<sub>k</sub> α<sub>k</sub> · A<sup>k</sup>)
                &nbsp;·&nbsp;
                α<sub>k</sub> = GAP(∂ŷ / ∂A<sup>k</sup>)
                &nbsp;·&nbsp;
                Upsampling bilineal 32×32 → 512×512
              </p>
            </div>
          </div>

          {/* Magnetic polarity chart */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="mb-4">
              <div className="text-[13px] font-semibold text-white">{m.magneticPolarity}</div>
              <div className="text-[11px] text-neutral-500 mt-0.5">
                {m.polaritySubtitle}
              </div>
            </div>

            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={polarity} margin={{ top: 5, right: 10, left: -10, bottom: 5 }} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#525252', fontSize: 9, fontFamily: 'monospace' }}
                    axisLine={false}
                    tickLine={false}
                    interval={Math.floor(polarity.length / 6)}
                  />
                  <YAxis
                    tick={{ fill: '#525252', fontSize: 9, fontFamily: 'monospace' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <ReferenceLine y={0} stroke="#404040" />
                  <RechartsTooltip
                    contentStyle={{
                      background: '#171717',
                      border: '1px solid #404040',
                      borderRadius: '8px',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                    }}
                    labelStyle={{ color: '#a3a3a3' }}
                    formatter={(value: number, name: string) => [
                      value.toFixed(4),
                      name === 'b_pos' ? m.positiveB : m.negativeB,
                    ]}
                  />
                  <Bar dataKey="b_pos" fill="#f97316" radius={[2, 2, 0, 0]} maxBarSize={12} />
                  <Bar dataKey="b_neg" fill="#3b82f6" radius={[0, 0, 2, 2]} maxBarSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="flex items-center gap-4 mt-2 px-1">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-sm bg-orange-500" />
                <span className="text-[10px] text-neutral-500 font-mono">{m.positiveB}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-sm bg-blue-500" />
                <span className="text-[10px] text-neutral-500 font-mono">{m.negativeB}</span>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
