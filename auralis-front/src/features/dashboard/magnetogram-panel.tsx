import { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronDown, Cpu, Eye, Zap, Upload, X } from 'lucide-react';

// ---------------------------------------------------------------------------
// Golden Samples — quick-access demo kit
// ---------------------------------------------------------------------------
const GOLDEN_SAMPLES = [
  {
    label: 'Normal',
    filename: 'hmi.m_45s.2016.11.12_00_01_30_TAI.magnetogram_processed.npy',
    si: '1.22',
    color: '#22c55e',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
  },
  {
    label: 'Moderate',
    filename: 'hmi.m_45s.2024.10.19_00_01_30_TAI.magnetogram_processed.npy',
    si: '1.85',
    color: '#f97316',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
  },
  {
    label: 'Extreme',
    filename: 'hmi.m_45s.2025.01.20_00_01_30_TAI.magnetogram_processed.npy',
    si: '2.76',
    color: '#ef4444',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
  },
] as const;
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  getImageList, getImageUrl, getAiaUrl, predictDual,
  getExplainPanelsUrl, getPolaritySeries,
  uploadImagePreview, predictUpload, explainPanelsUpload,
} from '@/lib/api';
import type { ImageListItem, PredictionResult } from '@/lib/types';
import type { PolarityPoint } from '@/lib/api';
import { useLanguage } from '@/lib/i18n/language-context';

/**
 * Interactive magnetogram workspace.
 *
 * This panel owns the highest-cost dashboard flows: image rendering, ONNX
 * inference, Grad-CAM generation, polarity charts, and upload-based black-box
 * tests. Backend endpoints remain the source of truth for preprocessing,
 * classification, and model output semantics.
 */

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

  // ── Black Box Test (drag & drop) state ───────────────────────────────────
  const [isDragging, setIsDragging] = useState(false);
  const [uploadPreviewUrl, setUploadPreviewUrl] = useState<string | null>(null);
  const [uploadPrediction, setUploadPrediction] = useState<PredictionResult | null>(null);
  const [uploadGradcamUrl, setUploadGradcamUrl] = useState<string | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadGradcamLoading, setUploadGradcamLoading] = useState(false);
  const [uploadGradcamOn, setUploadGradcamOn] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadFilename, setUploadFilename] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Upload preview and prediction are requested in parallel because they are
   * independent backend operations over the same `.npy` payload. Drag/drop
   * callers copy the file into the hidden input before invoking this helper so
   * a later Grad-CAM request can reuse the exact file object.
   */
  const processUploadedFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.npy')) {
      setUploadError('Only .npy files are accepted.');
      return;
    }
    // Reset previous state
    setUploadPreviewUrl(null);
    setUploadPrediction(null);
    setUploadGradcamUrl(null);
    setUploadGradcamOn(false);
    setUploadError(null);
    setUploadFilename(file.name);
    setUploadLoading(true);

    try {
      const [previewUrl, predResult] = await Promise.all([
        uploadImagePreview(file),
        predictUpload(file),
      ]);
      setUploadPreviewUrl(previewUrl);
      setUploadPrediction(predResult);
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploadLoading(false);
    }
  }, []);

  /**
   * Grad-CAM is deferred until the user asks for it. It requires the PyTorch
   * model and autograd hooks on the backend, so computing it eagerly would make
   * ordinary upload inference feel slower for no benefit.
   */
  const handleUploadGradcam = useCallback(async () => {
    if (!fileInputRef.current?.files?.[0] && uploadGradcamUrl) {
      setUploadGradcamOn(true);
      return;
    }
    if (uploadGradcamUrl) { setUploadGradcamOn((v) => !v); return; }
    if (!fileInputRef.current?.files?.[0]) return;
    setUploadGradcamLoading(true);
    try {
      const url = await explainPanelsUpload(fileInputRef.current.files[0]);
      setUploadGradcamUrl(url);
      setUploadGradcamOn(true);
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : 'Grad-CAM failed');
    } finally {
      setUploadGradcamLoading(false);
    }
  }, [uploadGradcamUrl]);

  const clearUpload = useCallback(() => {
    setUploadPreviewUrl(null);
    setUploadPrediction(null);
    setUploadGradcamUrl(null);
    setUploadGradcamOn(false);
    setUploadError(null);
    setUploadFilename(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

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
  const classification = prediction?.classification;
  const hexColor = classification?.hex_color ?? '#6b7280';
  const confPct = prediction ? prediction.confidence * 100 : 0;

  return (
    <div className="space-y-4">

      {/* ── Image selector ─────────────────────────────────────────── */}
      <div className="flex items-center gap-3 flex-wrap">
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

      {/* ── Quick Access — Golden Samples ──────────────────────────── */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 text-[10px] text-neutral-600 font-mono mr-1">
          <Zap className="w-3 h-3" />
          DEMO KIT
        </div>
        {GOLDEN_SAMPLES.map((s) => (
          <button
            key={s.label}
            onClick={() => setSelected(s.filename)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[11px] font-mono font-semibold transition-all ${
              selected === s.filename
                ? `${s.bg} ${s.border} ${s.text}`
                : 'bg-neutral-900 border-neutral-800 text-neutral-500 hover:border-neutral-700 hover:text-neutral-400'
            }`}
          >
            <span
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: s.color }}
            />
            {s.label}
            <span className="opacity-60">SI {s.si}</span>
          </button>
        ))}
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
              <div
                className="text-[38px] font-mono font-bold leading-none"
                style={{ color: hexColor }}
              >
                {prediction?.sunspot_index?.toFixed(2) ?? '—'}
              </div>
            )}
            <div className="text-[11px] text-neutral-500 mt-1">
              {m.predictedFlare}{' '}
              <span className="font-medium" style={{ color: hexColor }}>
                {classification ? `${classification.flare_class}-class` : '—'}
              </span>
            </div>
          </div>

          {/* Risk + Confidence */}
          <div className="grid grid-cols-2 gap-3">
            <div
              className="rounded-lg border p-3"
              style={{
                borderColor: `${hexColor}50`,
                backgroundColor: `${hexColor}18`,
              }}
            >
              <div className="text-[9px] text-neutral-500 tracking-[0.14em] mb-1.5">
                {m.riskLevel}
              </div>
              <div
                className="text-[18px] font-bold font-mono leading-tight"
                style={{ color: hexColor }}
              >
                {classification?.flare_class ?? '—'}
              </div>
              <div
                className="text-[9px] mt-0.5 font-medium truncate"
                style={{ color: hexColor }}
              >
                {classification?.label ?? '—'}
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
            <span className="text-neutral-300 font-mono">Coronium V3 PRO · v3.0</span>
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
                Bilinear upsampling 32×32 → 512×512
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

      {/* ── Black Box Test — Drag & Drop ───────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">

        {/* Section header */}
        <div className="px-5 py-3 border-b border-neutral-800 flex items-center justify-between">
          <div>
            <div className="text-[13px] font-semibold text-white flex items-center gap-2">
              <Upload className="w-4 h-4 text-neutral-400" />
              Black Box Test
            </div>
            <div className="text-[11px] text-neutral-500 mt-0.5">
              Drag & drop any processed .npy magnetogram — live ONNX inference + Grad-CAM
            </div>
          </div>
          <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
            OPEN
          </span>
        </div>

        <div className="p-5 space-y-4">

          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const file = e.dataTransfer.files?.[0];
              if (file) {
                // Store file in the hidden input so Grad-CAM can reuse it
                const dt = new DataTransfer();
                dt.items.add(file);
                if (fileInputRef.current) fileInputRef.current.files = dt.files;
                processUploadedFile(file);
              }
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center gap-3 py-10 cursor-pointer transition-all select-none ${
              isDragging
                ? 'border-orange-500/70 bg-orange-500/5'
                : 'border-neutral-700 bg-neutral-800/30 hover:border-neutral-600 hover:bg-neutral-800/50'
            }`}
          >
            <Upload className={`w-8 h-8 transition-colors ${isDragging ? 'text-orange-400' : 'text-neutral-600'}`} />
            <div className="text-center">
              <p className={`text-[13px] font-medium transition-colors ${isDragging ? 'text-orange-300' : 'text-neutral-400'}`}>
                {isDragging ? 'Drop to analyse' : 'Drop a .npy magnetogram here'}
              </p>
              <p className="text-[11px] text-neutral-600 mt-0.5 font-mono">
                or click to browse · float32 · (2, 512, 512) or (512, 512)
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".npy"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) processUploadedFile(file);
              }}
            />
          </div>

          {/* Results */}
          {(uploadLoading || uploadPrediction || uploadError) && (
            <div className="grid grid-cols-1 md:grid-cols-[1fr_360px] gap-4">

              {/* Magnetogram preview */}
              <div className="bg-neutral-950 border border-neutral-800 rounded-xl overflow-hidden">
                <div className="px-4 py-2.5 border-b border-neutral-800 flex items-center justify-between">
                  <span className="text-[11px] font-mono text-neutral-400 truncate max-w-[260px]">
                    {uploadFilename ?? 'uploaded file'}
                  </span>
                  <button
                    onClick={clearUpload}
                    className="text-neutral-600 hover:text-neutral-400 transition-colors ml-2 flex-shrink-0"
                    title="Clear"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="aspect-square bg-black">
                  {uploadLoading && !uploadPreviewUrl ? (
                    <div className="w-full h-full flex items-center justify-center text-neutral-600 text-xs font-mono">
                      Processing…
                    </div>
                  ) : uploadPreviewUrl ? (
                    <img
                      src={uploadPreviewUrl}
                      alt="Uploaded magnetogram"
                      className="w-full h-full object-contain"
                    />
                  ) : null}
                </div>
              </div>

              {/* Prediction card */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex flex-col gap-4">

                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-[14px] font-semibold text-white">Inference Result</div>
                    <div className="text-[11px] text-neutral-500 mt-0.5">ONNX · 20-pass MC</div>
                  </div>
                  {uploadPrediction && (
                    <span className="flex items-center gap-1.5 text-[11px] text-green-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                      OK
                    </span>
                  )}
                </div>

                {uploadLoading ? (
                  <div className="text-[38px] font-mono font-bold text-neutral-600">…</div>
                ) : uploadError ? (
                  <div className="text-[12px] text-red-400 font-mono break-all">{uploadError}</div>
                ) : uploadPrediction ? (
                  <>
                    <div>
                      <div className="text-[9px] text-neutral-500 tracking-[0.15em] mb-1">
                        SOLAR ACTIVITY INDEX
                      </div>
                      <div
                        className="text-[38px] font-mono font-bold leading-none"
                        style={{ color: uploadPrediction.classification?.hex_color ?? '#6b7280' }}
                      >
                        {uploadPrediction.sunspot_index?.toFixed(2) ?? '—'}
                      </div>
                      <div className="text-[11px] text-neutral-500 mt-1">
                        Predicted flare class:{' '}
                        <span
                          className="font-medium"
                          style={{ color: uploadPrediction.classification?.hex_color ?? '#6b7280' }}
                        >
                          {uploadPrediction.classification
                            ? `${uploadPrediction.classification.flare_class}-class`
                            : '—'}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div
                        className="rounded-lg border p-3"
                        style={{
                          borderColor: `${uploadPrediction.classification?.hex_color ?? '#6b7280'}50`,
                          backgroundColor: `${uploadPrediction.classification?.hex_color ?? '#6b7280'}18`,
                        }}
                      >
                        <div className="text-[9px] text-neutral-500 tracking-[0.14em] mb-1.5">RISK LEVEL</div>
                        <div
                          className="text-[18px] font-bold font-mono leading-tight"
                          style={{ color: uploadPrediction.classification?.hex_color ?? '#6b7280' }}
                        >
                          {uploadPrediction.classification?.flare_class ?? '—'}
                        </div>
                        <div
                          className="text-[9px] mt-0.5 font-medium truncate"
                          style={{ color: uploadPrediction.classification?.hex_color ?? '#6b7280' }}
                        >
                          {uploadPrediction.classification?.label ?? '—'}
                        </div>
                      </div>
                      <div className="rounded-lg border border-neutral-700 bg-neutral-800/50 p-3">
                        <div className="text-[9px] text-neutral-500 tracking-[0.14em] mb-1.5">CONFIDENCE</div>
                        <div className="text-[20px] font-bold font-mono text-white">
                          {(uploadPrediction.confidence * 100).toFixed(1)}%
                        </div>
                        <div className="mt-2 h-1 bg-neutral-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-orange-500 transition-all duration-700"
                            style={{ width: `${uploadPrediction.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Grad-CAM toggle */}
                    <button
                      onClick={handleUploadGradcam}
                      disabled={uploadGradcamLoading}
                      className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg border transition-colors disabled:opacity-50 ${
                        uploadGradcamOn
                          ? 'bg-orange-500/10 border-orange-500/50 text-orange-400'
                          : 'bg-neutral-800/60 border-neutral-700 text-neutral-400 hover:text-neutral-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 text-[12px] font-medium">
                        <Eye className="w-4 h-4" />
                        {uploadGradcamLoading ? 'Computing Grad-CAM…' : 'AI Vision (Grad-CAM)'}
                      </div>
                      <span className={`text-[11px] font-mono font-bold ${uploadGradcamOn ? 'text-orange-400' : 'text-neutral-600'}`}>
                        {uploadGradcamLoading ? '…' : uploadGradcamOn ? 'ON' : 'OFF'}
                      </span>
                    </button>

                    <div className="flex items-center gap-1.5 text-[11px] text-neutral-500 py-2 border-t border-neutral-800">
                      <Cpu className="w-3.5 h-3.5" />
                      <span>Coronium V3 PRO · ONNX Runtime · 86.6 KB</span>
                    </div>
                  </>
                ) : null}
              </div>
            </div>
          )}

          {/* Grad-CAM panel for upload */}
          {uploadGradcamOn && uploadGradcamUrl && (
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-neutral-800 flex items-center justify-between">
                <div>
                  <div className="text-[13px] font-semibold text-white">Grad-CAM · Black Box</div>
                  <div className="text-[11px] text-neutral-500 mt-0.5">
                    Attention heatmap — stage4.conv · K=96
                  </div>
                </div>
                <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
                  XAI
                </span>
              </div>
              <div className="bg-black p-1">
                <img
                  src={uploadGradcamUrl}
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
                  Bilinear upsampling 32×32 → 512×512
                </p>
              </div>
            </div>
          )}

        </div>
      </div>

    </div>
  );
}
