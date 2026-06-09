import { ArrowRight, Github, ExternalLink } from 'lucide-react';
import { useEffect, useState } from 'react';
import { RippleButton } from '@/components/shared/ripple-button';
import { getStats } from '@/lib/api';
import type { SystemStats } from '@/lib/types';

interface LandingHeroProps {
  /** Invoked when the user clicks the primary CTA; parent swaps to the dashboard view. */
  onEnterDashboard: () => void;
}

/**
 * Landing hero section: animated starfield backdrop plus live model stats
 * (sample count and R²) fetched from the backend `/api/stats` endpoint.
 *
 * @param props.onEnterDashboard - Callback fired when the "Enter dashboard" CTA is clicked.
 */
export function LandingHero({ onEnterDashboard }: LandingHeroProps) {
  const [stats, setStats] = useState<SystemStats | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => null);
  }, []);

  const accuracyProxy = '93.93%';
  const samples = stats ? `${stats.total_images.toLocaleString()} imgs` : '—';
  const r2 = stats ? `R² ${stats.r2_score.toFixed(2)}` : '—';

  return (
    <div
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden"
      style={{ background: '#04040f' }}
    >
      {/* Starfield */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 150 }).map((_, i) => {
          const size = Math.random() * 2 + 0.5;
          return (
            <div
              key={i}
              className="absolute rounded-full bg-white"
              style={{
                width: `${size}px`,
                height: `${size}px`,
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                opacity: Math.random() * 0.6 + 0.2,
                animation: `lh-twinkle ${Math.random() * 4 + 2}s ease-in-out ${Math.random() * 5}s infinite`,
              }}
            />
          );
        })}
      </div>

      {/* NASA Sun GIF — full background */}
      <img
        src="/sun.gif"
        alt="Sun"
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{
          objectFit: 'cover',
          objectPosition: 'center',
          opacity: 0.55,
          filter: 'brightness(1.1) saturate(1.3)',
          zIndex: 1,
        }}
      />

      {/* Dark overlay so text is readable */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 100% 100% at 50% 50%, rgba(4,4,15,0.25) 0%, rgba(4,4,15,0.7) 100%)',
          zIndex: 2,
        }}
      />

      {/* Main content — centered */}
      <div className="relative flex flex-col items-center text-center px-6" style={{ zIndex: 4 }}>

        {/* AURALIS title */}
        <h1
          className="font-black uppercase"
          style={{
            fontSize: 'clamp(4rem, 14vw, 9rem)',
            letterSpacing: '0.12em',
            color: '#f5c518',
            textShadow: '0 0 40px rgba(245,197,24,0.7), 0 0 100px rgba(245,150,0,0.35)',
            lineHeight: 1,
          }}
        >
          Auralis
        </h1>

        {/* Subtitle */}
        <p
          className="text-white font-semibold uppercase tracking-widest mt-3"
          style={{ fontSize: 'clamp(0.85rem, 2.5vw, 1.2rem)' }}
        >
          Solar Activity Analysis System
        </p>
        <p className="text-neutral-400 text-sm mt-2">
          AI · NASA SDO/HMI · Coronium V3 PRO
        </p>

        {/* CTA buttons */}
        <div className="flex items-center justify-center gap-4 mt-8 flex-wrap">
          <RippleButton
            variant="primary"
            onClick={onEnterDashboard}
            className="!px-8 !py-3 text-sm"
          >
            View Dashboard
            <ArrowRight className="w-4 h-4 ml-2" />
          </RippleButton>

          <a
            href="https://github.com/Alehcs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-8 py-3 border border-white/15 text-white text-sm transition-colors hover:bg-white/5 rounded"
            style={{ background: '#000' }}
          >
            <Github className="w-4 h-4" />
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3 ml-1 text-neutral-500" />
          </a>
        </div>

        {/* Tech strip */}
        <div className="mt-10 flex items-center justify-center gap-2 text-xs flex-wrap">
          {[
            ['Data Source', 'NASA SDO/HMI'],
            ['Dataset', samples],
            ['Model', 'Coronium V3 PRO'],
            ['Accuracy proxy', accuracyProxy],
            ['R²', r2],
          ].map(([label, value], i, arr) => (
            <div key={label} className="flex items-center gap-2">
              <span className="text-neutral-500">{label}:</span>
              <span className="text-white font-mono">{value}</span>
              {i < arr.length - 1 && <span className="text-neutral-700 mx-2">·</span>}
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes lh-twinkle {
          0%, 100% { opacity: 0.15; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
