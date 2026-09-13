import { useEffect, useRef, useState } from 'react';

const VIEWER = new URL(import.meta.env.VITE_SOLAR_VIEWER_URL || '/phase6/', location.origin);

export function SolarTwinPanel() {
  const frame = useRef<HTMLIFrameElement>(null);
  const [attempt, setAttempt] = useState(0);
  const [status, setStatus] = useState<'loading'|'ready'|'error'>('loading');
  const [height, setHeight] = useState(1000);
  useEffect(() => {
    let timer = window.setTimeout(() => setStatus('error'), 60000);
    const receive = (event: MessageEvent) => {
      if (event.origin !== VIEWER.origin || event.source !== frame.current?.contentWindow || event.data?.type !== 'auralis-viewer') return;
      const data = event.data;
      if (data.status === 'ready' || data.status === 'error') { window.clearTimeout(timer); setStatus(data.status); }
      if (typeof data.height === 'number' && Number.isFinite(data.height)) setHeight(Math.max(800, Math.min(12000, data.height + 2)));
    };
    window.addEventListener('message', receive);
    return () => { window.clearTimeout(timer); window.removeEventListener('message', receive); };
  }, [attempt]);
  return <section aria-label="Gemelo solar Unity/Needle" className="space-y-3">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h1 className="text-xl font-semibold text-white">Gemelo solar</h1></div>

    </div>

    {status === 'loading' && <p role="status" className="text-sm text-neutral-300">Cargando visor…</p>}
    {status === 'error' ? <div role="alert" className="rounded-xl border border-neutral-700 p-6 text-neutral-200">
      <p>No se pudo cargar el visor.</p>
      <button className="mt-3 rounded-lg border border-neutral-600 px-4 py-3" onClick={() => { setStatus('loading'); setAttempt(n=>n+1); }}>Reintentar</button>
    </div> : <iframe key={attempt} ref={frame} title="Gemelo solar aprobado · Unity y Needle" src={VIEWER.href} referrerPolicy="origin"
      allow={`xr-spatial-tracking ${VIEWER.origin}; camera ${VIEWER.origin}; fullscreen ${VIEWER.origin}`} allowFullScreen
      className="block w-full rounded-xl border border-neutral-800 bg-[#090b10]" style={{height}} />}
  </section>;
}
