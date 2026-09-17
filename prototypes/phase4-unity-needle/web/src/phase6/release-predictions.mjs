// Numerical release overlay only. Original observation/visual manifests remain authoritative.
import {digest} from '../phase5/contract.mjs';
export const RELEASE_SHA256='915bdca52e0db568556620e78a70b84cc9f2a0056c27e4ea2c5d8fcf1207f1ed';
export function applyReleasePredictions(sequence, release){
  if(release.schema_version!=='auralis.coronium-predictions.v1'||release.model?.version!=='3.2'||
     release.model.seed!==42||release.model.epoch!==27||release.entries?.length!==5||
     release.source_contract_sha256!==sequence.contract_sha256||
     release.runtime?.session_config?.['mlas.disable_kleidiai']!=='1')throw Error('Release numérico incompatible.');
  const next=structuredClone(sequence);
  for(const [i,entry] of next.entries.entries()){
    const result=release.entries[i],state=entry.state;
    if(result.state_id!==state.id||result.filename!==state.observation.magnetogram.filename||
       result.prior_v31_prediction!==state.coronium_results.prediction_si||!Number.isFinite(result.prediction_si))throw Error('Identidad temporal del release incorrecta.');
    state.coronium_results={...state.coronium_results,model_ref:release.model.id,
      protocol:release.protocol,prediction_si:result.prediction_si,api_display_4dp:result.api_display_4dp,
      source_ref:'models/coronium_v3_2_temporal.json',
      grad_cam:{...state.coronium_results.grad_cam,reason:'No frozen temporal Grad-CAM for this release.'}};
  }
  next.model=release.model;
  return next;
}
export async function selectReleasePredictions(sequence,fetchBytes,search,defaultVersion='3.1'){
  const version=new URLSearchParams(search).get('release') ?? defaultVersion;
  if(version===null||version==='3.1')return sequence;
  if(version!=='3.2')throw Error('Versión de resultados no disponible.');
  const bytes=await fetchBytes('/phase6/releases/coronium-v3.2-r1.json');
  if(await digest(bytes)!==RELEASE_SHA256)throw Error('Integridad del release numérico incorrecta.');
  return applyReleasePredictions(sequence,JSON.parse(new TextDecoder().decode(bytes)));
}
