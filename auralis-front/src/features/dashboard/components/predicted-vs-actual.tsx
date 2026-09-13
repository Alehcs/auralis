import { useState, useEffect } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Label,
} from 'recharts';
import { getResultsComparison } from '@/lib/api';
import { useLanguage } from '@/lib/i18n/language-context';

interface DataPoint {
  real: number;
  predicted: number;
  error: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: { payload: DataPoint }[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-xs font-mono shadow-lg">
      <div className="flex justify-between gap-4">
        <span className="text-neutral-400">Real:</span>
        <span className="text-white">{d.real.toFixed(3)}</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-neutral-400">Predicted:</span>
        <span className="text-cyan-300">{d.predicted.toFixed(3)}</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-neutral-400">|Error|:</span>
        <span className={d.error > 0.5 ? 'text-red-400' : 'text-green-400'}>
          {d.error.toFixed(3)}
        </span>
      </div>
    </div>
  );
}

export function PredictedVsActual() {
  const { t } = useLanguage();
  const e = t.experiments;

  const [data,    setData]    = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [protocol, setProtocol] = useState<'mc' | 'deterministic'>('mc');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getResultsComparison(protocol)
      .then((values) => { if (active) setData(values); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [protocol]);

  const values = data.flatMap((point) => [point.real, point.predicted]);
  const axisMin = values.length ? Math.floor((Math.min(...values) - 0.05) * 10) / 10 : 0;
  const axisMax = values.length ? Math.ceil((Math.max(...values) + 0.05) * 10) / 10 : 1;

  const diagonalLine = [
    { real: axisMin, predicted: axisMin },
    { real: axisMax, predicted: axisMax },
  ];

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 flex items-start justify-between border-b border-neutral-800">
        <div>
          <div className="text-[15px] font-semibold text-white">{e.predVsReal}</div>
          <div className="text-[11px] text-neutral-500 mt-0.5">
            {e.diagonalNote}
          </div>
        </div>
        <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
          V3.1 · {protocol === 'mc' ? 'MC T=20 · MPS' : 'ONNX eval · CPU'} · N={loading ? '—' : data.length}
        </span>
      </div>

      <div className="p-5">
        <label className="text-xs text-neutral-400 flex items-center gap-3 mb-3">
          Protocol
          <select aria-label="Evaluation protocol" value={protocol} onChange={(event) => setProtocol(event.target.value as 'mc' | 'deterministic')} className="bg-neutral-800 rounded px-2 py-1 text-white">
            <option value="mc">MC Dropout T=20 · batch 32 · seed 42</option>
            <option value="deterministic">Deterministic ONNX · batch 1</option>
          </select>
        </label>
        <p className="text-[11px] text-neutral-500 mb-3">Selection validation · no independent or temporal test. SI = % of original pixels with |B LOS| &gt; 200 G.</p>
        {loading && (
          <div className="flex items-center justify-center h-72 text-neutral-600 text-sm">
            {e.loading}
          </div>
        )}

        {error && (
          <div className="bg-red-950/50 border border-red-900/50 rounded-lg px-3 py-2 text-xs text-red-400">
            {error}
          </div>
        )}

        {!loading && !error && data.length > 0 && (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 35, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis
                  type="number"
                  dataKey="real"
                  domain={[axisMin, axisMax]}
                  tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={{ stroke: '#404040' }}
                  tickLine={false}
                  tickFormatter={(v: number) => v.toFixed(1)}
                >
                  <Label
                    value="Target SI (%)"
                    position="insideBottom"
                    offset={-20}
                    style={{ fill: '#737373', fontSize: 11, fontFamily: 'monospace' }}
                  />
                </XAxis>
                <YAxis
                  type="number"
                  dataKey="predicted"
                  domain={[axisMin, axisMax]}
                  tick={{ fill: '#525252', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) => v.toFixed(1)}
                  width={36}
                >
                  <Label
                    value="Predicted SI (%)"
                    angle={-90}
                    position="insideLeft"
                    offset={12}
                    style={{ fill: '#737373', fontSize: 11, fontFamily: 'monospace' }}
                  />
                </YAxis>
                <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#404040' }} />

                {/* y = x diagonal — orange dashed */}
                <Scatter
                  data={diagonalLine}
                  line={{ stroke: '#f97316', strokeDasharray: '6 4', strokeWidth: 1.5 }}
                  shape={() => <g />}
                  legendType="none"
                />

                {/* Data points — cyan */}
                <Scatter
                  data={data}
                  shape={(props: unknown) => {
                    const p = props as { cx?: number; cy?: number };
                    const { cx = 0, cy = 0 } = p;
                    return (
                      <circle
                        cx={cx} cy={cy} r={3.5}
                        fill="#38bdf8"
                        fillOpacity={0.7}
                        stroke="#38bdf8"
                        strokeWidth={0.5}
                      />
                    );
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
