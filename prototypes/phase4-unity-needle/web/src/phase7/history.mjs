export function eventRelation(event, states) {
  const peak=Date.parse(event.peak_utc);
  const before=states.filter(s=>Date.parse(s.record_utc)<=peak).at(-1);
  const after=states.find(s=>Date.parse(s.record_utc)>peak);
  return {basis:'peak_utc',placement:after?'between_states':'after_last_state',
    preceding_state_id:before?.id??null,following_state_id:after?.id??null,
    seconds_after_preceding_state:before?(peak-Date.parse(before.record_utc))/1000:null,
    captured_by_state_id:null};
}
export function validateContext(context, sequence, sequenceHash) {
  if(context?.schema_version!=='auralis.phase7.v1'||context.contract_sha256!==sequence.contract_sha256||context.sequence_sha256!==sequenceHash||context.states?.length!==5||context.events?.length!==6)throw Error('Procedencia del contexto científico incorrecta.');
  const sources=new Map(context.sources.map(s=>[s.id,s]));
  for(const s of sources.values())if(!/^[a-f0-9]{64}$/.test(s.sha256)||s.snapshot_url!=='/phase7/sources/'+s.path.split('/').at(-1)||!/^https?:\/\//.test(s.url))throw Error('Fuente científica incorrecta.');
  for(const [i,s] of context.states.entries()){
    const original=sequence.entries[i].state,r=s.region_context;
    if(s.id!==original.id||s.record_utc!==original.observation.time.record_utc||JSON.stringify(r)!==JSON.stringify(original.observation.region_context)||!sources.has(r.location.source_ref)||!sources.has(r.harp_source_ref))throw Error('Contexto SRS no corresponde al estado HMI.');
  }
  const ids=['20220328_3390','20220328_3570','20220329_3630','20220329_3990','20220330_4220','20220331_4520'];
  const classes=['M4.0','M1.1','M2.2','M1.6','X1.3','M9.6'];
  for(const [i,e] of context.events.entries()){
    const times=[e.start_utc,e.peak_utc,e.end_utc].map(Date.parse),r=eventRelation(e,context.states);
    if(e.id!==ids[i]||e.goes_class!==classes[i]||e.noaa!==12975||e.type!=='GOES_XRA_1_8A'||e.kind!=='observational_event'||e.association!=='NOAA_catalog_region_context_not_model_prediction'||!sources.has(e.source_ref)||times.some(t=>!Number.isFinite(t))||times[0]>times[1]||times[1]>times[2]||Object.entries(r).some(([key,value])=>e.temporal_relation[key]!==value))throw Error('Evento histórico o relación temporal incorrectos.');
  }
  const x=context.events[4];
  if(x.peak_utc!=='2022-03-30T17:37:00Z'||x.temporal_relation.seconds_after_preceding_state!==63367||x.temporal_relation.following_state_id!==null)throw Error('La X1.3 debe quedar 17 h 36 min 07 s después del último HMI.');
  return context;
}
export function timeDomain(context){return [Date.parse(context.states[0].record_utc),Math.max(...context.events.map(e=>Date.parse(e.end_utc)),...context.states.map(s=>Date.parse(s.record_utc)))];}
export function position(utc,domain){return (Date.parse(utc)-domain[0])/(domain[1]-domain[0]);}
// Lanes only avoid label collisions; the horizontal peak time is NEVER moved.
export function eventLayout(context,width=900,labelWidth=124){
  const domain=timeDomain(context),ends=[];
  return context.events.map(e=>{const p=position(e.peak_utc,domain);let lane=ends.findIndex(end=>p*width-end>=labelWidth);if(lane<0)lane=ends.length;ends[lane]=p*width;return {id:e.id,position:p,lane};});
}
export function elapsed(seconds){const h=Math.floor(seconds/3600),m=Math.floor(seconds%3600/60),s=seconds%60;return `${h} h ${String(m).padStart(2,'0')} min ${String(s).padStart(2,'0')} s`;}
export function dateLabel(utc){return new Intl.DateTimeFormat('es-CL',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(utc));}
export function utcLabel(utc){return dateLabel(utc)+' '+utc.slice(11,19)+' UTC';}
