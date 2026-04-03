import { GitBranch } from 'lucide-react';

interface FoldResult {
  fold: number;
  mae: number;
  rmse: number;
  r2: number;
}

const FOLD_DATA: FoldResult[] = [
  { fold: 1, mae: 0.1389, rmse: 0.1821, r2: 0.8734 },
  { fold: 2, mae: 0.1452, rmse: 0.1893, r2: 0.8651 },
  { fold: 3, mae: 0.1418, rmse: 0.1847, r2: 0.8712 },
  { fold: 4, mae: 0.1401, rmse: 0.1836, r2: 0.8728 },
  { fold: 5, mae: 0.1421, rmse: 0.1858, r2: 0.8698 },
];

// Pre-computed summary row
const SUMMARY = {
  mae:  { mean: 0.1416, std: 0.0022 },
  rmse: { mean: 0.1851, std: 0.0025 },
  r2:   { mean: 0.8705, std: 0.0029 },
};

function fmt(n: number, decimals = 4): string {
  return n.toFixed(decimals);
}

function r2Color(value: number): string {
  if (value >= 0.87) return 'text-green-400';
  if (value >= 0.86) return 'text-blue-400';
  return 'text-neutral-300';
}

export function KFoldResults() {
  return (
    <div className="bg-neutral-950 border border-neutral-800">
      <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-neutral-400" />
          <div>
            <h2 className="text-sm font-semibold text-white">Validación Cruzada K-Fold (k=5)</h2>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              Estabilidad del modelo ante distintas particiones temporales · SolarNet V2 PRO
            </p>
          </div>
        </div>
      </div>

      <div className="p-4">
        <div className="border border-neutral-800 overflow-hidden">
          <table className="w-full text-sm font-mono">
            <thead>
              <tr className="bg-neutral-900 border-b border-neutral-800">
                <th className="text-left px-4 py-2.5 text-[11px] text-neutral-500 font-medium w-20">Fold</th>
                <th className="text-right px-4 py-2.5 text-[11px] text-neutral-500 font-medium">MAE (%)</th>
                <th className="text-right px-4 py-2.5 text-[11px] text-neutral-500 font-medium">RMSE (%)</th>
                <th className="text-right px-4 py-2.5 text-[11px] text-neutral-500 font-medium">R² Score</th>
              </tr>
            </thead>
            <tbody>
              {FOLD_DATA.map((row, idx) => (
                <tr
                  key={row.fold}
                  className={`border-b border-neutral-800/60 transition-colors hover:bg-neutral-900/50 ${
                    idx % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900/30'
                  }`}
                >
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 bg-neutral-800 border border-neutral-700 flex items-center justify-center">
                        <span className="text-[10px] text-neutral-400">{row.fold}</span>
                      </div>
                      <span className="text-[11px] text-neutral-500">Fold {row.fold}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-right text-neutral-300 text-xs">{fmt(row.mae)}</td>
                  <td className="px-4 py-2.5 text-right text-neutral-300 text-xs">{fmt(row.rmse)}</td>
                  <td className={`px-4 py-2.5 text-right text-xs font-semibold ${r2Color(row.r2)}`}>
                    {fmt(row.r2)}
                  </td>
                </tr>
              ))}

              {/* Summary row */}
              <tr className="bg-neutral-900 border-t-2 border-neutral-700">
                <td className="px-4 py-3">
                  <span className="text-[11px] text-white font-bold">Promedio ± Std</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs text-white font-bold">{fmt(SUMMARY.mae.mean)}</span>
                  <span className="text-[10px] text-neutral-500 font-normal ml-1">
                    ± {fmt(SUMMARY.mae.std)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs text-white font-bold">{fmt(SUMMARY.rmse.mean)}</span>
                  <span className="text-[10px] text-neutral-500 font-normal ml-1">
                    ± {fmt(SUMMARY.rmse.std)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs text-green-400 font-bold">{fmt(SUMMARY.r2.mean)}</span>
                  <span className="text-[10px] text-neutral-500 font-normal ml-1">
                    ± {fmt(SUMMARY.r2.std)}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span className="text-[10px] text-neutral-500 font-mono">R² ≥ 0.87</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            <span className="text-[10px] text-neutral-500 font-mono">R² ≥ 0.86</span>
          </div>
          <span className="text-[10px] text-neutral-600 font-mono ml-auto">
            Baja varianza entre folds — modelo estable
          </span>
        </div>
      </div>
    </div>
  );
}
