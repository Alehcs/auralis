import { ImageWithFallback } from '@/components/figma/ImageWithFallback';
import { Maximize2, Download } from 'lucide-react';
import { RippleButton } from '@/components/shared/ripple-button';

interface MagnetogramVizProps {
  imageUrl: string;
}

export function MagnetogramViz({ imageUrl }: MagnetogramVizProps) {
  const detections = [
    { id: 1, x: 25, y: 30, width: 15, height: 15, confidence: 0.94 },
    { id: 2, x: 60, y: 45, width: 18, height: 18, confidence: 0.89 },
    { id: 3, x: 40, y: 65, width: 12, height: 12, confidence: 0.87 },
  ];

  return (
    <div className="bg-black/40 border border-white/10 rounded-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">SDO/HMI Magnetogram Analysis</h2>
          <p className="text-sm text-gray-400">Real-time sunspot detection • Updated 3 minutes ago</p>
        </div>
        <div className="flex space-x-2">
          <RippleButton variant="ghost" className="!px-3 !py-2">
            <Maximize2 className="w-4 h-4" />
          </RippleButton>
          <RippleButton variant="ghost" className="!px-3 !py-2">
            <Download className="w-4 h-4" />
          </RippleButton>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="relative aspect-square rounded-lg overflow-hidden bg-black/60 border border-white/10">
          <ImageWithFallback
            src={imageUrl}
            alt="Solar Magnetogram"
            className="w-full h-full object-cover"
          />
          <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-sm px-3 py-1 rounded text-xs text-white">
            Original
          </div>
        </div>

        <div className="relative aspect-square rounded-lg overflow-hidden bg-black/60 border border-white/10">
          <ImageWithFallback
            src={imageUrl}
            alt="Solar Magnetogram with Detections"
            className="w-full h-full object-cover"
          />
          {detections.map((detection) => (
            <div
              key={detection.id}
              className="absolute border-2 border-orange-500 rounded animate-pulse"
              style={{
                left: `${detection.x}%`,
                top: `${detection.y}%`,
                width: `${detection.width}%`,
                height: `${detection.height}%`,
              }}
            >
              <div className="absolute -top-6 left-0 bg-orange-500 text-white text-xs px-2 py-0.5 rounded">
                {(detection.confidence * 100).toFixed(0)}%
              </div>
            </div>
          ))}
          <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-sm px-3 py-1 rounded text-xs text-white">
            Detection Overlay
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mt-6">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <p className="text-xs text-gray-400 mb-1">Detected Spots</p>
          <p className="text-xl font-bold text-white">12</p>
        </div>
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <p className="text-xs text-gray-400 mb-1">Avg Confidence</p>
          <p className="text-xl font-bold text-green-400">91.2%</p>
        </div>
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <p className="text-xs text-gray-400 mb-1">Processing Time</p>
          <p className="text-xl font-bold text-blue-400">1.3s</p>
        </div>
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <p className="text-xs text-gray-400 mb-1">Model Version</p>
          <p className="text-xl font-bold text-white">3.2.1</p>
        </div>
      </div>
    </div>
  );
}
