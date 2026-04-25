import { useLanguage } from '@/lib/i18n/language-context';

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

const SUMMARY = {
  mae:  { mean: 0.1416, std: 0.0022 },
  rmse: { mean: 0.1851, std: 0.0025 },
  r2:   { mean: 0.8705, std: 0.0029 },
};

function fmt(n: number) { return n.toFixed(4); }

export function KFoldResults() {
  const { t } = useLanguage();
  const e = t.experiments;

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-neutral-800 flex items-start justify-between">
        <div>
          <div className="text-[15px] font-semibold text-white">{e.kfold}</div>
        </div>
        <span className="text-[10px] font-mono text-neutral-400 bg-neutral-800 border border-neutral-700 px-2.5 py-1 rounded-lg">
          K = 5
        </span>
      </div>

      {/* Table */}
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-neutral-800">
            <th className="text-left px-5 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colFold}</th>
            <th className="text-right px-4 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colMae}</th>
            <th className="text-right px-4 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colRmse}</th>
            <th className="text-right px-5 py-3 text-[10px] text-neutral-500 font-medium tracking-[0.12em]">{e.colR2}</th>
          </tr>
        </thead>
        <tbody>
          {FOLD_DATA.map((row, idx) => (
            <tr
              key={row.fold}
              className={`border-b border-neutral-800/50 ${idx % 2 === 0 ? '' : 'bg-neutral-800/20'}`}
            >
              <td className="px-5 py-3 text-neutral-300">{e.colFold} {row.fold}</td>
              <td className="px-4 py-3 text-right text-neutral-300">{fmt(row.mae)}</td>
              <td className="px-4 py-3 text-right text-neutral-300">{fmt(row.rmse)}</td>
              <td className="px-5 py-3 text-right text-neutral-300">{fmt(row.r2)}</td>
            </tr>
          ))}

          {/* Summary */}
          <tr className="border-t-2 border-neutral-700 bg-neutral-800/30">
            <td className="px-5 py-3 text-white font-semibold">{e.avgStd}</td>
            <td className="px-4 py-3 text-right">
              <span className="text-white font-semibold">{fmt(SUMMARY.mae.mean)}</span>
              <span className="text-neutral-600 ml-1">± {fmt(SUMMARY.mae.std)}</span>
            </td>
            <td className="px-4 py-3 text-right">
              <span className="text-white font-semibold">{fmt(SUMMARY.rmse.mean)}</span>
              <span className="text-neutral-600 ml-1">± {fmt(SUMMARY.rmse.std)}</span>
            </td>
            <td className="px-5 py-3 text-right">
              <span className="text-green-400 font-semibold">{fmt(SUMMARY.r2.mean)}</span>
              <span className="text-neutral-600 ml-1">± {fmt(SUMMARY.r2.std)}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
