/**
 * Types and tuning profiles for the educational solar simulation tab.
 *
 * Everything here is procedural and illustrative: activity classes C/M/X are
 * used as *visual intensity presets*, not as physical flare classifications or
 * forecasts. No Coronium model output feeds this module.
 */

export type ActivityClass = 'C' | 'M' | 'X';

export interface SimulationToggles {
  sunspots: boolean;
  magneticRegions: boolean;
  magnetogram: boolean;
}

/** Visual preset applied per activity class. Purely aesthetic knobs. */
export interface ActivityProfile {
  /** Number of bipolar active regions painted on the surface. */
  regionCount: number;
  /** Angular radius range (radians) of each region patch. */
  regionRadius: [number, number];
  /** Sunspot darkening size multiplier. */
  spotScale: number;
  /** Corona / rim glow strength. */
  glowIntensity: number;
  /** Surface noise churn speed multiplier. */
  turbulence: number;
  /** Min/max ms between automatic flare-like visual events. */
  flareIntervalMs: [number, number];
  /** Arc height + brightness multiplier for flare-like events. */
  flareStrength: number;
}

export const ACTIVITY_PROFILES: Record<ActivityClass, ActivityProfile> = {
  C: {
    regionCount: 3,
    regionRadius: [0.10, 0.16],
    spotScale: 0.75,
    glowIntensity: 0.55,
    turbulence: 0.7,
    flareIntervalMs: [9000, 16000],
    flareStrength: 0.65,
  },
  M: {
    regionCount: 7,
    regionRadius: [0.12, 0.20],
    spotScale: 1.0,
    glowIntensity: 0.8,
    turbulence: 1.0,
    flareIntervalMs: [5000, 9000],
    flareStrength: 1.0,
  },
  X: {
    regionCount: 12,
    regionRadius: [0.14, 0.24],
    spotScale: 1.35,
    glowIntensity: 1.15,
    turbulence: 1.45,
    flareIntervalMs: [2500, 5000],
    flareStrength: 1.5,
  },
};
