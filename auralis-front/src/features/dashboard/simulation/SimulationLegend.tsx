/**
 * Legend for the procedural solar simulation. Swatches map the rendered
 * visual elements (surface, sunspots, active regions, flare-like arcs) and,
 * when magnetogram mode is active, the B+/B− grayscale polarity convention.
 */

import { useLanguage } from '@/lib/i18n/language-context';

function LegendRow({ swatch, label, desc }: { swatch: React.ReactNode; label: string; desc: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex-shrink-0">{swatch}</div>
      <div className="min-w-0">
        <div className="text-[12px] text-neutral-300 leading-tight">{label}</div>
        <div className="text-[10.5px] text-neutral-500 leading-snug mt-0.5">{desc}</div>
      </div>
    </div>
  );
}

function Dot({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={`w-4 h-4 rounded-full border border-neutral-700 ${className ?? ''}`} style={style} />;
}

export function SimulationLegend({ magnetogram }: { magnetogram: boolean }) {
  const { t } = useLanguage();
  const s = t.simulation;

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      <div className="text-[11px] text-neutral-400 font-mono mb-3">{s.legend}</div>

      {magnetogram ? (
        <div className="space-y-3">
          <LegendRow
            swatch={<Dot className="bg-white" />}
            label={s.legendBPlus}
            desc={s.legendBPlusDesc}
          />
          <LegendRow
            swatch={<Dot className="bg-black" />}
            label={s.legendBMinus}
            desc={s.legendBMinusDesc}
          />
          <LegendRow
            swatch={<Dot className="bg-neutral-500" />}
            label={s.legendNeutral}
            desc={s.legendNeutralDesc}
          />
          <div className="pt-2 border-t border-neutral-800">
            <p className="text-[10px] text-neutral-500 leading-snug">{s.magnetogramDisclaimer}</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <LegendRow
            swatch={<Dot style={{ background: 'radial-gradient(circle, #ffd166 0%, #f97316 60%, #9a3412 100%)' }} />}
            label={s.legendSurface}
            desc={s.legendSurfaceDesc}
          />
          <LegendRow
            swatch={<Dot style={{ background: 'radial-gradient(circle, #1a0d00 0%, #7c2d12 100%)' }} />}
            label={s.legendSunspot}
            desc={s.legendSunspotDesc}
          />
          <LegendRow
            swatch={<Dot style={{ background: 'radial-gradient(circle, #ffedd5 0%, #fb923c 70%)' }} />}
            label={s.legendRegion}
            desc={s.legendRegionDesc}
          />
          <LegendRow
            swatch={<Dot style={{ background: 'linear-gradient(135deg, #fff7ed 0%, #fdba74 100%)' }} />}
            label={s.legendFlare}
            desc={s.legendFlareDesc}
          />
        </div>
      )}
    </div>
  );
}
