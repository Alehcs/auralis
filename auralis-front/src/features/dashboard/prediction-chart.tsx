import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer,
} from 'recharts';
import { Database, Calendar, Layers } from 'lucide-react';
import { getImageList } from '@/lib/api';
import { useLanguage } from '@/lib/i18n/language-context';

interface YearCount {
  year: string;
  count: number;
}

// ---------------------------------------------------------------------------
// Gradient bar shape
// ---------------------------------------------------------------------------
function GradientBar(props: {
  x?: number; y?: number; width?: number; height?: number;
  [key: string]: unknown;
}) {
  const { x = 0, y = 0, width = 0, height = 0 } = props;
  if (!height || height <= 0) return null;
  return (
    <g>
      <defs>
        <linearGradient id="solar-bar-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#fbbf24" stopOpacity={1} />
          <stop offset="100%" stopColor="#dc2626" stopOpacity={1} />
        </linearGradient>
      </defs>
      <rect
        x={x} y={y}
        width={width} height={height}
        fill="url(#solar-bar-grad)"
        rx={3} ry={3}
      />
    </g>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function PredictionChart() {
  const { t } = useLanguage();
  const p = t.pipeline;
  const [data,    setData]    = useState<YearCount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getImageList()
      .then((res) => {
        const counts: Record<string, number> = {};
        for (const img of res.images) {
          if (img.date) {
            const year = img.date.substring(0, 4);
            counts[year] = (counts[year] || 0) + 1;
          }
        }
        const sorted = Object.entries(counts)
          .map(([year, count]) => ({ year, count }))
          .sort((a, b) => a.year.localeCompare(b.year));
        setData(sorted);
      })
      .finally(() => setLoading(false));
  }, []);

  const totalImages = data.reduce((s, d) => s + d.count, 0);
  const firstYear   = data.length > 0 ? data[0].year : '—';
  const lastYear    = data.length > 0 ? data[data.length - 1].year : '—';
  const yearRange   = data.length > 0 ? `${firstYear} — ${lastYear}` : '—';
  const yearsSpan   = data.length > 0
    ? parseInt(lastYear) - parseInt(firstYear) + 1
    : 0;
  const avgPerYear  = data.length > 0
    ? Math.round(totalImages / data.length)
    : 0;

  const CARDS = [
    {
      label:     p.totalImages,
      value:     loading ? '—' : totalImages.toLocaleString(),
      sub:       p.acrossChannels,
      Icon:      Database,
      iconBg:    'bg-orange-500/20',
      iconColor: 'text-orange-400',
    },
    {
      label:     p.yearRange,
      value:     loading ? '—' : yearRange,
      sub:       loading ? `— ${p.yearsOfSdo}` : `${yearsSpan} ${p.yearsOfSdo}`,
      Icon:      Calendar,
      iconBg:    'bg-teal-500/20',
      iconColor: 'text-teal-400',
    },
    {
      label:     p.avgPerYear,
      value:     loading ? '—' : avgPerYear.toLocaleString(),
      sub:       p.annually,
      Icon:      null,
      iconBg:    'bg-purple-500/20',
      iconColor: 'text-purple-400',
    },
    {
      label:     p.channels,
      value:     '2',
      sub:       p.hmiChannels,
      Icon:      Layers,
      iconBg:    'bg-amber-500/20',
      iconColor: 'text-amber-400',
    },
  ] as const;

  return (
    <div className="space-y-4">

      {/* ── Metric cards ──────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        {CARDS.map((card) => (
          <div
            key={card.label}
            className="bg-neutral-900 border border-neutral-800 rounded-xl p-5"
          >
            <div className="flex items-start justify-between">
              <div className="text-[9px] text-neutral-500 tracking-[0.15em] font-mono">
                {card.label}
              </div>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${card.iconBg}`}>
                {card.Icon
                  ? <card.Icon className={`w-4 h-4 ${card.iconColor}`} />
                  : <span className={`text-[16px] font-bold leading-none ${card.iconColor}`}>Σ</span>
                }
              </div>
            </div>
            <div className="text-[30px] font-mono font-bold text-white mt-3 leading-none tracking-tight">
              {card.value}
            </div>
            <div className="text-[11px] text-neutral-500 mt-2">{card.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Bar chart ─────────────────────────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-[15px] font-semibold text-white">{p.chartTitle}</div>
            <div className="text-[11px] text-neutral-500 mt-0.5">{p.chartSubtitle}</div>
          </div>
          <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
            {p.pipeline}
          </span>
        </div>

        <div className="h-80">
          {loading ? (
            <div className="w-full h-full flex items-center justify-center text-neutral-600 text-sm">
              {p.loading}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                barCategoryGap="25%"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                <XAxis
                  dataKey="year"
                  tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={false}
                  tickLine={false}
                />
                <RechartsTooltip
                  contentStyle={{
                    background: '#171717',
                    border: '1px solid #404040',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    color: '#ffffff',
                  }}
                  labelStyle={{ color: '#a3a3a3' }}
                  itemStyle={{ color: '#ffffff' }}
                  formatter={(value: number) => [value.toLocaleString(), p.images]}
                />
                {/* @ts-expect-error custom shape */}
                <Bar dataKey="count" shape={<GradientBar />} maxBarSize={44} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

    </div>
  );
}
