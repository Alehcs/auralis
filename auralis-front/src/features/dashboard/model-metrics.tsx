import { useState, useEffect } from 'react';
import {
  Sigma,
  ImageIcon,
  HardDrive,
  Activity,
  CheckCircle2,
  AlertTriangle,
  CalendarDays,
  Layers,
  ScanLine,
  Timer,
} from 'lucide-react';
import { getStats, getImageList, predictDual } from '@/lib/api';
import type { SystemStats, PredictionResult } from '@/lib/types';
import { useLanguage } from '@/lib/i18n/language-context';

/**
 * Overview panel for promoted model metrics and dataset-derived current state.
 *
 * "Current Solar State" is intentionally based on the newest processed `.npy`
 * file returned by the backend. It should not be described as live NASA
 * telemetry unless the ingestion layer is changed to support that contract.
 */

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ActivityBadge({
  hexColor,
  label,
}: {
  hexColor: string;
  label: string;
}) {
  return (
    <span
      className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium border"
      style={{
        color: hexColor,
        borderColor: `${hexColor}50`,
        backgroundColor: `${hexColor}18`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: hexColor }}
      />
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Metric card
// ---------------------------------------------------------------------------

interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
  trend?: string;
  trendUp?: boolean;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
}

function MetricCard({ label, value, unit, trend, trendUp, icon: Icon, iconBg, iconColor }: MetricCardProps) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <span className="text-[10px] text-neutral-500 tracking-[0.12em] uppercase">{label}</span>
        <div className={`w-8 h-8 rounded-lg border flex items-center justify-center flex-shrink-0 ${iconBg}`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className="text-[28px] font-mono font-semibold text-white leading-none">{value}</span>
        {unit && <span className="text-[12px] text-neutral-500 font-mono">{unit}</span>}
      </div>

      {trend && (
        <div className={`flex items-center gap-1 text-[11px] font-mono ${trendUp ? 'text-green-400' : 'text-neutral-500'}`}>
          {trendUp && <span>↗</span>}
          <span>{trend}</span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status row
// ---------------------------------------------------------------------------

function StatusRow({ label, status, labels }: {
  label: string;
  status: 'nominal' | 'degraded' | 'offline';
  labels: { nominal: string; degraded: string; offline: string };
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-neutral-800/60 last:border-0">
      <span className="text-[12px] text-neutral-400">{label}</span>
      {status === 'nominal' ? (
        <span className="flex items-center gap-1.5 text-[11px] text-green-400">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {labels.nominal}
        </span>
      ) : status === 'degraded' ? (
        <span className="flex items-center gap-1.5 text-[11px] text-orange-400">
          <AlertTriangle className="w-3.5 h-3.5" />
          {labels.degraded}
        </span>
      ) : (
        <span className="flex items-center gap-1.5 text-[11px] text-red-400">
          <AlertTriangle className="w-3.5 h-3.5" />
          {labels.offline}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ModelMetrics() {
  const { t } = useLanguage();
  const o = t.overview;

  const [stats, setStats]           = useState<SystemStats | null>(null);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [latestFile, setLatestFile] = useState<string>('—');
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    // Static promoted-run metrics and dynamic dataset footprint.
    getStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setStatsLoading(false));

    // Latest-file inference drives the current-state card.
    getImageList()
      .then((res) => {
        if (res.images.length === 0) return;
        const img = res.images[0];
        setLatestFile(img.date ?? img.filename);
        return predictDual(img.filename).then(setPrediction).catch(console.error);
      })
      .catch(console.error);
  }, []);

  // Derived
  const activityIndex  = prediction?.sunspot_index?.toFixed(2) ?? '—';
  const classification = prediction?.classification;
  const hexColor       = classification?.hex_color ?? '#6b7280';
  const activityLabel  = classification?.label ?? o.lowRisk;
  const confidence     = prediction ? `${(prediction.confidence * 100).toFixed(1)}%` : '—';
  const mae           = stats ? stats.mae.toFixed(4) : '—';
  const totalImages   = stats ? stats.total_images.toLocaleString() : '—';
  const diskGb        = stats ? (stats.disk_usage_mb / 1024).toFixed(2) : '—';
  const diskMb        = stats?.disk_usage_mb ?? 0;

  // Disk allocation bar (max 20 GB display cap)
  const MAX_DISK_MB = 20_000;
  const diskPct     = Math.min((diskMb / MAX_DISK_MB) * 100, 100);

  const statusLabels = { nominal: o.nominal, degraded: o.degraded, offline: o.offline };

  return (
    <div className="space-y-4">

      {/* ── Hero: Current Solar State ──────────────────────────── */}
      <div className="relative overflow-hidden rounded-xl bg-neutral-900 border border-neutral-800 px-7 py-6">
        {/* Warm glow overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'radial-gradient(ellipse at 85% 50%, rgba(146,64,14,0.28) 0%, transparent 65%)',
          }}
        />

        <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Left */}
          <div>
            <div className="text-[10px] text-neutral-500 tracking-[0.18em] mb-2">
              {o.currentState}
            </div>
            <div className="flex items-baseline gap-3 mb-2">
              <span className="text-[13px] font-medium text-neutral-300">{o.activityIndex}</span>
              <span
                className="text-[42px] font-mono font-bold leading-none"
                style={{ color: hexColor }}
              >
                {statsLoading ? '…' : activityIndex}
              </span>
            </div>
            <div className="text-[12px] text-neutral-500">
              {o.predictedBy}{' '}
              <span className="text-neutral-300 font-medium">Coronium V3 PRO</span>{' '}
              · {latestFile}
            </div>
          </div>

          {/* Right: badges */}
          <div className="flex flex-row sm:flex-col items-start sm:items-end gap-2 flex-shrink-0">
            <ActivityBadge hexColor={hexColor} label={activityLabel} />
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-transparent border border-green-600/50 text-green-400 text-[11px] font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {o.systemNominal}
            </span>
          </div>
        </div>
      </div>

      {/* ── 4 Metric cards ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <MetricCard
          label={o.modelMae}
          value={mae}
          trend={o.physicalScale}
          icon={Sigma}
          iconBg="bg-orange-500/10 border-orange-500/20"
          iconColor="text-orange-400"
        />
        <MetricCard
          label={o.processedImages}
          value={totalImages}
          trend={o.since2010}
          trendUp={!!stats}
          icon={ImageIcon}
          iconBg="bg-blue-500/10 border-blue-500/20"
          iconColor="text-blue-400"
        />
        <MetricCard
          label={o.diskUsage}
          value={diskGb}
          unit="GB"
          trend={`${stats?.disk_usage_mb.toFixed(0) ?? '—'} ${o.mbTotal}`}
          icon={HardDrive}
          iconBg="bg-amber-500/10 border-amber-500/20"
          iconColor="text-amber-400"
        />
        <MetricCard
          label={o.confidence}
          value={confidence}
          trend={o.mcDropout}
          trendUp={!!prediction}
          icon={Activity}
          iconBg="bg-violet-500/10 border-violet-500/20"
          iconColor="text-violet-400"
        />
      </div>

      {/* ── Dataset summary + System status ────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 md:gap-4">

        {/* Dataset summary (2/3) */}
        <div className="lg:col-span-2 bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[13px] font-semibold text-white">{o.datasetSummary}</span>
            <span className="text-[10px] font-mono text-neutral-500 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
              SDO / HMI · AIA
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { icon: CalendarDays, label: o.years,      value: '2010 — 2024' },
              { icon: Layers,       label: o.channels,   value: '2 (B+/B−)' },
              { icon: ScanLine,     label: o.resolution, value: '512²' },
              { icon: Timer,        label: o.cadence,    value: '45 s' },
            ].map(({ icon: Icon, label, value }) => (
              <div
                key={label}
                className="bg-neutral-950 border border-neutral-800 rounded-lg p-3 flex flex-col gap-2"
              >
                <div className="flex items-center gap-1.5">
                  <Icon className="w-3.5 h-3.5 text-neutral-600" />
                  <span className="text-[9px] text-neutral-600 tracking-[0.14em]">{label}</span>
                </div>
                <span className="text-[15px] font-mono text-white font-medium leading-none">
                  {value}
                </span>
              </div>
            ))}
          </div>

          {/* Disk allocation bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] text-neutral-500">{o.diskAllocation}</span>
              <span className="text-[11px] font-mono text-neutral-400">{diskGb} {o.diskUsed}</span>
            </div>
            <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${diskPct}%`,
                  background: 'linear-gradient(to right, #22c55e, #f59e0b, #ef4444)',
                }}
              />
            </div>
          </div>
        </div>

        {/* System status (1/3) */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <div className="text-[13px] font-semibold text-white mb-4">{o.systemStatus}</div>
          <div>
            <StatusRow label={o.inferenceWorker} status="nominal"  labels={statusLabels} />
            <StatusRow label={o.sdoIngestion}    status="nominal"  labels={statusLabels} />
            <StatusRow label={o.modelRegistry}   status="nominal"  labels={statusLabels} />
            <StatusRow label={o.gradcamEngine}   status="nominal"  labels={statusLabels} />
            <StatusRow label={o.experimentStore} status="nominal"  labels={statusLabels} />
          </div>
        </div>
      </div>
    </div>
  );
}
