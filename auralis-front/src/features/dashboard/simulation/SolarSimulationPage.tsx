/**
 * Simulación / Simulation tab — public-facing educational visualization.
 *
 * Interactive procedural 3D Sun for explaining solar rotation, activity
 * levels, sunspots, active regions, flare-like events and B+/B− magnetogram
 * polarity in the context of the Coronium V3 dashboard. Explicitly NOT a
 * physical plasma simulation, forecast, or real SDO/HMI imagery — every panel
 * carries that disclaimer, and nothing here reads or writes model artifacts.
 */

import { useRef, useState } from 'react';
import { Info, Orbit, Sun, Magnet, Waves, RotateCcw } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/language-context';
import { SolarScene, type SolarSceneHandle } from './SolarScene';
import { SimulationControls } from './SimulationControls';
import { SimulationLegend } from './SimulationLegend';
import type { ActivityClass, SimulationToggles } from './solarSimulationTypes';

const CLASS_CHIP: Record<ActivityClass, string> = {
  C: 'border-amber-500/40 text-amber-300 bg-amber-500/10',
  M: 'border-orange-500/40 text-orange-300 bg-orange-500/10',
  X: 'border-red-500/40 text-red-300 bg-red-500/10',
};

function ExplainerCard({ icon: Icon, title, body }: {
  icon: typeof Sun; title: string; body: string;
}) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 hover:border-neutral-700 transition-colors rounded-xl p-5">
      <div className="flex items-center gap-2.5 mb-2">
        <div className="w-8 h-8 rounded-lg bg-orange-500/15 flex items-center justify-center flex-shrink-0">
          <Icon className="w-4 h-4 text-orange-400" />
        </div>
        <div className="text-[13px] font-semibold text-white">{title}</div>
      </div>
      <p className="text-[11.5px] text-neutral-500 leading-snug">{body}</p>
    </div>
  );
}

function CanvasButton({ label, active, onClick, children }: {
  label: string; active?: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      title={label}
      aria-label={label}
      onClick={onClick}
      className={`w-8 h-8 rounded-lg border backdrop-blur flex items-center justify-center transition-colors ${
        active
          ? 'bg-orange-500/20 border-orange-500/50 text-orange-300'
          : 'bg-black/60 border-neutral-800 text-neutral-400 hover:text-white hover:border-neutral-600'
      }`}
    >
      {children}
    </button>
  );
}

export function SolarSimulationPage() {
  const { t } = useLanguage();
  const s = t.simulation;

  const [activity, setActivity] = useState<ActivityClass>('M');
  const [toggles, setToggles] = useState<SimulationToggles>({
    sunspots: true,
    magneticRegions: true,
    magnetogram: false,
  });
  const [autoRotate, setAutoRotate] = useState(false);
  const sceneRef = useRef<SolarSceneHandle>(null);

  return (
    <div className="space-y-4">

      {/* ── Header ────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-[20px] font-bold text-white tracking-tight">{s.title}</h1>
        <p className="text-[12.5px] text-neutral-500 mt-1 max-w-3xl leading-snug">{s.subtitle}</p>
        <div className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-neutral-800 bg-neutral-900/60">
          <span className="w-[6px] h-[6px] rounded-full bg-orange-500 flex-shrink-0" />
          <span className="text-[10px] text-neutral-500 tracking-wide">{s.educationalBadge}</span>
        </div>
      </div>

      {/* ── Canvas + side panel ───────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4">

        {/* 3D canvas card */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col">
          <div className="px-5 py-3.5 border-b border-neutral-800 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[13px] font-semibold text-white">{s.canvasTitle}</div>
              <div className="text-[10.5px] text-neutral-500 mt-0.5">{s.canvasSubtitle}</div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${CLASS_CHIP[activity]}`}>
                {activity}
              </span>
              <span className="text-[9px] text-neutral-600 font-mono tracking-[0.14em] uppercase">
                {s.proceduralTag}
              </span>
            </div>
          </div>
          <div className="relative flex-1 min-h-[380px] md:min-h-[480px] bg-black">
            <SolarScene
              ref={sceneRef}
              activity={activity}
              sunspots={toggles.sunspots}
              magneticRegions={toggles.magneticRegions}
              magnetogram={toggles.magnetogram}
              autoRotate={autoRotate}
            />
            <div className="absolute top-3 right-3 flex gap-2">
              <CanvasButton label={s.autoRotate} active={autoRotate} onClick={() => setAutoRotate((v) => !v)}>
                <Orbit className="w-4 h-4" />
              </CanvasButton>
              <CanvasButton label={s.resetView} onClick={() => sceneRef.current?.resetView()}>
                <RotateCcw className="w-4 h-4" />
              </CanvasButton>
            </div>
            {toggles.magnetogram && (
              <div className="absolute bottom-3 left-3 right-3 pointer-events-none">
                <div className="inline-block px-3 py-1.5 rounded-lg bg-black/70 border border-neutral-800">
                  <span className="text-[10px] text-neutral-400">{s.magnetogramDisclaimer}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Controls + legend */}
        <div className="space-y-4 min-w-0">
          <SimulationControls
            activity={activity}
            onActivityChange={setActivity}
            toggles={toggles}
            onTogglesChange={setToggles}
            onTriggerFlare={() => sceneRef.current?.triggerFlare()}
          />
          <SimulationLegend magnetogram={toggles.magnetogram} />
        </div>
      </div>

      {/* ── Explanation panel ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <ExplainerCard icon={Orbit}  title={s.explainRotationTitle} body={s.explainRotationBody} />
        <ExplainerCard icon={Waves}  title={s.explainActivityTitle} body={s.explainActivityBody} />
        <ExplainerCard icon={Sun}    title={s.explainSunspotsTitle} body={s.explainSunspotsBody} />
        <ExplainerCard icon={Magnet} title={s.explainPolarityTitle} body={s.explainPolarityBody} />
      </div>

      {/* ── Global disclaimer ─────────────────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-neutral-800 flex items-center justify-center flex-shrink-0">
          <Info className="w-4 h-4 text-neutral-400" />
        </div>
        <p className="text-[11.5px] text-neutral-500 leading-snug">{s.disclaimer}</p>
      </div>
    </div>
  );
}
