/**
 * Control panel for the educational solar simulation: visual activity class
 * presets (C/M/X), overlay toggles, and a manual flare-like event trigger.
 * All controls drive procedural visuals only — nothing here touches Coronium.
 */

import { Zap } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/language-context';
import type { ActivityClass, SimulationToggles } from './solarSimulationTypes';

const ACTIVITY_STYLES: Record<ActivityClass, { active: string; dot: string }> = {
  C: { active: 'bg-amber-500/10 border-amber-500/50 text-amber-300',   dot: 'bg-amber-400'  },
  M: { active: 'bg-orange-500/10 border-orange-500/50 text-orange-300', dot: 'bg-orange-400' },
  X: { active: 'bg-red-500/10 border-red-500/50 text-red-300',          dot: 'bg-red-400'    },
};

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0 ${on ? 'bg-orange-500' : 'bg-neutral-600'}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${on ? 'translate-x-5' : 'translate-x-0'}`} />
    </button>
  );
}

function ToggleRow({ label, sublabel, on, onChange }: {
  label: string; sublabel: string; on: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3 bg-neutral-800/40 border border-neutral-700/50 rounded-xl">
      <div className="min-w-0">
        <div className="text-[13px] text-neutral-300">{label}</div>
        <div className="text-[10.5px] text-neutral-500 mt-0.5 leading-snug">{sublabel}</div>
      </div>
      <Toggle on={on} onChange={onChange} />
    </div>
  );
}

interface SimulationControlsProps {
  activity: ActivityClass;
  onActivityChange: (cls: ActivityClass) => void;
  toggles: SimulationToggles;
  onTogglesChange: (next: SimulationToggles) => void;
  onTriggerFlare: () => void;
}

export function SimulationControls({
  activity, onActivityChange, toggles, onTogglesChange, onTriggerFlare,
}: SimulationControlsProps) {
  const { t } = useLanguage();
  const s = t.simulation;

  const CLASSES: { id: ActivityClass; desc: string }[] = [
    { id: 'C', desc: s.classCDesc },
    { id: 'M', desc: s.classMDesc },
    { id: 'X', desc: s.classXDesc },
  ];

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-5">

      {/* ── Visual activity level ────────────────────────────────── */}
      <div>
        <div className="text-[11px] text-neutral-400 font-mono mb-3">{s.activityLevel}</div>
        <div className="grid grid-cols-3 gap-2">
          {CLASSES.map(({ id, desc }) => {
            const active = activity === id;
            const style = ACTIVITY_STYLES[id];
            return (
              <button
                key={id}
                onClick={() => onActivityChange(id)}
                className={`px-2 py-3 rounded-xl border text-center transition-all duration-150 active:scale-[0.97] ${
                  active
                    ? style.active
                    : 'bg-neutral-800/40 border-neutral-700/50 text-neutral-400 hover:border-neutral-600 hover:bg-neutral-800/70'
                }`}
              >
                <div className="flex items-center justify-center gap-1.5">
                  <span className={`w-[6px] h-[6px] rounded-full ${active ? style.dot : 'bg-neutral-600'}`} />
                  <span className="text-[15px] font-bold">{id}</span>
                </div>
                <div className="text-[9.5px] mt-1 text-neutral-500 leading-tight">{desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Manual flare-like event ──────────────────────────────── */}
      <button
        onClick={onTriggerFlare}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-orange-500/40 bg-orange-500/10 text-orange-300 hover:bg-orange-500/20 hover:border-orange-500/60 active:scale-[0.98] transition-all duration-150"
      >
        <Zap className="w-4 h-4" />
        <span className="text-[13px] font-semibold">{s.triggerEvent}</span>
      </button>

      {/* ── Overlays ─────────────────────────────────────────────── */}
      <div className="space-y-2">
        <div className="text-[11px] text-neutral-400 font-mono mb-1">{s.overlays}</div>
        <ToggleRow
          label={s.magneticRegions}
          sublabel={s.magneticRegionsDesc}
          on={toggles.magneticRegions}
          onChange={(v) => onTogglesChange({ ...toggles, magneticRegions: v })}
        />
        <ToggleRow
          label={s.sunspots}
          sublabel={s.sunspotsDesc}
          on={toggles.sunspots}
          onChange={(v) => onTogglesChange({ ...toggles, sunspots: v })}
        />
        <ToggleRow
          label={s.magnetogramView}
          sublabel={s.magnetogramViewDesc}
          on={toggles.magnetogram}
          onChange={(v) => onTogglesChange({ ...toggles, magnetogram: v })}
        />
      </div>
    </div>
  );
}
