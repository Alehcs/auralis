import type { PredictionResult } from './types';

export const IS_FROZEN_DEMO = import.meta.env.VITE_FROZEN_DEMO === 'true';
// Saved SI responses may lack the auxiliary input-noise diagnostic.
// This presentation type does not change the backend's response contract.
export type DisplayPredictionResult = Omit<PredictionResult, 'confidence' | 'uncertainty'> & {
  confidence: number | null;
  uncertainty: number | null;
};
let snapshot: Promise<Record<string, unknown>> | undefined;
export async function frozenResponse<T>(path: string): Promise<T> {
  snapshot ??= fetch('/demo/responses.json').then(async response => {
    if (!response.ok) throw new Error('No se pudo cargar la copia guardada de la demo.');
    return response.json();
  }).catch(error => { snapshot = undefined; throw error; });
  const responses = await snapshot;
  if (!Object.hasOwn(responses, path)) throw new Error('No hay un resultado guardado para esta operación. La demo no ejecuta análisis nuevos.');
  return responses[path] as T;
}
export function requireLiveBackend() {
  if (IS_FROZEN_DEMO) throw new Error('La demo de Sites no sube archivos ni ejecuta inferencias.');
}
