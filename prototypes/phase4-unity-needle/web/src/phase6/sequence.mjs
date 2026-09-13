export const CHANNELS=['magnetogram','bplus','bminus'];
export function validateSequence(m){
  if(m?.schema_version!=='auralis.phase6.v1'||m.entries?.length!==5)throw Error('Se requieren los cinco estados del contrato.');
  const dates=['2022-03-24','2022-03-25','2022-03-28','2022-03-29','2022-03-30'];
  for(const [i,e]of m.entries.entries()){
    const s=e.state,date=dates[i];
    if(s.id!=='hmi-'+date||s.order!==i+1||s.observation.id!==s.id+'-observation'||s.observation.time.record_utc!==date+'T00:00:53.000Z'||!s.observation.magnetogram.filename.includes(date.replaceAll('-','.')))throw Error('Orden, archivo o fecha temporal incorrectos.');
    if(!Number.isFinite(s.observation.target_si.value)||!Number.isFinite(s.coronium_results.prediction_si)||s.coronium_results.protocol!=='deterministic_onnx_cpu_eval_batch1_threads4_no_noise_no_mc')throw Error('Resultado o protocolo incorrecto.');
    const p=s.derived.polarity,r=s.observation.region_context;
    if(p.channel_order.join(',')!=='B_plus,B_minus_magnitude'||p.b_plus_mean<0||p.b_minus_magnitude_mean<0||r.wcs!==null||r.region_mask!==null||r.magnetic_field_3d!==null||s.coronium_results.grad_cam.status!=='not_available')throw Error('Contrato espacial o polaridades incorrectas.');
    for(const key of CHANNELS){const l=e.layers[key];if(l.url!==`/phase6/assets/${s.id}/${key}.png`||!/^[a-f0-9]{64}$/.test(l.sha256)||l.origin!=='upper_left_array_row0'||l.width!==512||l.height!==512)throw Error('Mapa temporal incorrecto.');}
  }
  if(m.visual.data_projection!=='none')throw Error('Proyección espacial no permitida.');
  return m;
}
export function nextIndex(index,direction,count=5){return Math.max(0,Math.min(count-1,index+direction));}
export function timelinePositions(entries){const t=entries.map(e=>Date.parse(e.state.observation.time.record_utc));return t.map(x=>(x-t[0])/(t.at(-1)-t[0]));}
