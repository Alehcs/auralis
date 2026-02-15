import { ArrowRight, Github, ExternalLink } from 'lucide-react';
import { RippleButton } from '@/components/shared/ripple-button';

interface LandingHeroProps {
  onEnterDashboard: () => void;
}

export function LandingHero({ onEnterDashboard }: LandingHeroProps) {
  return (
    <div className="relative min-h-[70vh] flex items-center justify-center px-6 py-20 overflow-hidden">
      {/* Subtle background */}
      <div className="absolute inset-0 bg-gradient-to-b from-neutral-950 via-neutral-900 to-neutral-950 opacity-50" />
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)',
          backgroundSize: '32px 32px'
        }} />
      </div>

      <div className="relative z-10 max-w-4xl mx-auto text-center">
        {/* Badge */}
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-neutral-900 border border-neutral-800 mb-6">
          <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs text-neutral-400 font-mono">SYSTEM OPERATIONAL</span>
        </div>

        {/* Title */}
        <h1 className="text-6xl font-bold text-white mb-4 tracking-tight">
          HeliosPipeline
        </h1>

        {/* Subtitle */}
        <p className="text-xl text-neutral-300 mb-6 max-w-3xl mx-auto">
          Machine Learning pipeline for solar activity prediction using NASA SDO/HMI magnetograms
        </p>

        {/* Description */}
        <p className="text-sm text-neutral-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          Real-time detection and forecasting of sunspot activity through computer vision and data engineering pipelines.
        </p>

        {/* Buttons */}
        <div className="flex items-center justify-center space-x-4">
          <RippleButton
            variant="primary"
            onClick={onEnterDashboard}
            className="!px-8 !py-3 text-sm"
          >
            View Live Dashboard
            <ArrowRight className="w-4 h-4 ml-2" />
          </RippleButton>

          <button className="flex items-center space-x-2 px-6 py-3 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-white text-sm transition-colors">
            <Github className="w-4 h-4" />
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3 ml-1 text-neutral-500" />
          </button>
        </div>

        {/* Tech specs strip */}
        <div className="mt-16 flex items-center justify-center space-x-8 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-neutral-500">Data Source:</span>
            <span className="text-white font-mono">NASA SDO/HMI</span>
          </div>
          <div className="w-1 h-1 bg-neutral-700 rounded-full" />
          <div className="flex items-center space-x-2">
            <span className="text-neutral-500">Forecast:</span>
            <span className="text-white font-mono">72 hours</span>
          </div>
          <div className="w-1 h-1 bg-neutral-700 rounded-full" />
          <div className="flex items-center space-x-2">
            <span className="text-neutral-500">Model:</span>
            <span className="text-white font-mono">CNN-ResNet50</span>
          </div>
        </div>
      </div>
    </div>
  );
}
