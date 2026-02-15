import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';
import { getImageList } from '@/lib/api';
import { useLanguage } from '@/lib/i18n/language-context';

interface YearCount {
  year: string;
  count: number;
}

export function PredictionChart() {
  const { t } = useLanguage();
  const [data, setData] = useState<YearCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getImageList()
      .then((res) => {
        // Group images by year from their date field
        const counts: Record<string, number> = {};
        for (const img of res.images) {
          if (img.date) {
            const year = img.date.substring(0, 4);
            counts[year] = (counts[year] || 0) + 1;
          }
        }
        // Sort by year ascending
        const sorted = Object.entries(counts)
          .map(([year, count]) => ({ year, count }))
          .sort((a, b) => a.year.localeCompare(b.year));
        setData(sorted);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-neutral-950 border border-neutral-800">
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">{t.predictionChart.title}</h2>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              {t.predictionChart.subtitle}
            </p>
          </div>
          <div className="flex items-center space-x-2 text-[11px]">
            <span className="text-neutral-500">{t.predictionChart.yearsCovered}:</span>
            <span className="font-mono text-white">{data.length}</span>
          </div>
        </div>
      </div>

      <div className="p-4">
        {error && (
          <div className="bg-red-950 border border-red-900 px-3 py-2 text-xs text-red-400 mb-4">
            {error}
          </div>
        )}

        <div className="h-80 bg-neutral-900 border border-neutral-800 p-4">
          {loading ? (
            <div className="w-full h-full flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-neutral-500 animate-spin" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 20, bottom: 25, left: 45 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                <XAxis
                  dataKey="year"
                  stroke="#737373"
                  tick={{ fill: '#a3a3a3', fontSize: 11 }}
                  label={{ value: t.predictionChart.observationYear, position: 'insideBottom', offset: -15, fill: '#a3a3a3', fontSize: 11 }}
                />
                <YAxis
                  stroke="#737373"
                  tick={{ fill: '#a3a3a3', fontSize: 11 }}
                  label={{ value: t.predictionChart.imageCount, angle: -90, position: 'insideLeft', fill: '#a3a3a3', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#171717',
                    border: '1px solid #404040',
                    borderRadius: '2px',
                    fontSize: '11px',
                    fontFamily: 'IBM Plex Mono, monospace',
                  }}
                  labelStyle={{ color: '#a3a3a3' }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-neutral-900 border border-neutral-800 p-3">
            <div className="text-[11px] text-neutral-500 mb-1">{t.predictionChart.totalImages}</div>
            <div className="text-xl font-mono text-white">
              {data.reduce((sum, d) => sum + d.count, 0).toLocaleString()}
            </div>
          </div>
          <div className="bg-neutral-900 border border-neutral-800 p-3">
            <div className="text-[11px] text-neutral-500 mb-1">{t.predictionChart.yearRange}</div>
            <div className="text-xl font-mono text-white">
              {data.length > 0 ? `${data[0].year} - ${data[data.length - 1].year}` : '--'}
            </div>
          </div>
          <div className="bg-neutral-900 border border-neutral-800 p-3">
            <div className="text-[11px] text-neutral-500 mb-1">{t.predictionChart.avgPerYear}</div>
            <div className="text-xl font-mono text-white">
              {data.length > 0
                ? Math.round(data.reduce((sum, d) => sum + d.count, 0) / data.length).toLocaleString()
                : '--'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
