import './style.css';
import QRCode from 'qrcode';
import { SurfaceClock, SURFACE_SEED } from '../phase6/surface-motion.mjs';
import { TemporalSequence } from '../phase6/temporal';
import { ScientificContext } from '../phase7/scientific-context.mjs';
import { validateContext } from '../phase7/history.mjs';
import '../phase7/scientific-context.css';
import { polishMaterials } from './visual-materials';
import { Mesh, Object3D, Vector3 } from 'three';
import { Context, OrbitControls, WebXR, WebARSessionRoot, USDZExporter, setActive } from '@needle-tools/engine';
import { summarizeFrames } from '../render-sample.mjs';
import { describeAR, shareable } from '../capabilities.mjs';
import { checkedLayer, clampScale, digest, validateState, verifyExport } from './contract.mjs';

const $ = <T extends HTMLElement = HTMLElement>(id:string)=>document.getElementById(id) as T;
const isTemporal=document.body.dataset.phase==='6';
let temporal:TemporalSequence|undefined;
let scientific:ScientificContext|undefined;
const assetBase=isTemporal?'/phase5/':'./';
const abort = new AbortController();
const events:Record<string,unknown>[]=[];
const samples:Record<string,unknown>[]=[];
const diag:Record<string,unknown>={build:isTemporal?'phase71-v1':'phase5-visual-polish-v1',engine:'5.1.12',source:'waiting-for-real-unity',errors:[],physicalValidation:'not_tested',placementCount:0,layer:'solar'};
const ios=/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
let context:Context|undefined, object:Object3D|undefined, orbit:OrbitControls|undefined;
let element:HTMLElement|undefined, removePlaced:(()=>void)|undefined;
let data:any, evidence:any, layer='solar', scale=1, automatic=false, started=0, lastFrame=-1, lastStats=0;
let timer:ReturnType<typeof setTimeout>|undefined;
let sample:{start:number;mode:string;times:number[];timer:ReturnType<typeof setTimeout>}|undefined;
let displayGain=4, plasma=!matchMedia('(prefers-reduced-motion: reduce)').matches, visual:ReturnType<typeof polishMaterials>|undefined, visualTime=0, visualLast=0;
const surfaceClock=new SurfaceClock(plasma);
let surfaceVisible=true;
let loading=false, released=false, attempt=0;
let sceneUrl:string|undefined;
const cleanupCallbacks:(()=>void)[]=[];
const verifiedUrls=new Map<string,string>();
const cameraOrigin=new Vector3();
const rootPosition=new Vector3();
function record(type:string){events.push({type,elapsedMs:Math.round(performance.now())});if(events.length>500)events.shift();}
function buttons(enabled:boolean){for(const b of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-layer],#zoom-in,#zoom-out,#reset,#auto,#sample,#release,#scale,#plasma,#surface-reset,[data-surface-toggle],[data-surface-reset],#contrast')))b.disabled=!enabled;}
function fail(error:unknown){const message=error instanceof Error?error.message:String(error);(diag.errors as string[]).push(message);$('load-status').textContent=message;$('retry').hidden=false;diag.status='failed';buttons(false);$('diagnostics').textContent=JSON.stringify(diag,null,2);}
const listen=(target:EventTarget,type:string,callback:EventListener)=>target.addEventListener(type,callback,{signal:abort.signal});
listen(window,'error',(e)=>fail((e as ErrorEvent).message));
listen(window,'unhandledrejection',(e)=>fail((e as PromiseRejectionEvent).reason));
function stopSample(reason='completed'){
  if(!sample)return;
  const current=sample;sample=undefined;clearTimeout(current.timer);
  const result={mode:current.mode,status:reason,layer,build:diag.build,surfaceMotion:plasma,stateId:data?.state.id,pixelRatio:context?.renderer.getPixelRatio(),cameraPosition:context?.mainCamera.position.toArray(),...summarizeFrames(current.times,performance.now()-current.start)};
  samples.push(result);if(samples.length>120)samples.shift();$('sample-result').textContent=JSON.stringify(result,null,2);$('sample').removeAttribute('disabled');
}
function startSample(){
  if(!context||released)return;
  if(sample)stopSample('restarted');
  sample={start:performance.now(),mode:context.renderer.xr.isPresenting?'xr':'web3d',times:[],timer:setTimeout(()=>stopSample(),30000)};
  ($<HTMLButtonElement>('sample')).disabled=true;$('sample-result').textContent='Midiendo 30 s de callbacks de render. Mantén el visor visible.';
  $('viewport').scrollIntoView({block:'center',behavior:'smooth'});record('sample-start');
}
listen(document,'visibilitychange',()=>{record('visibility:'+document.visibilityState);surfaceClock.sync(performance.now());visualLast=performance.now();if(document.hidden)temporal?.pause();if(document.hidden&&sample&&!context?.renderer.xr.isPresenting)stopSample('interrupted-hidden');});
$('sample').onclick=startSample;
const modes:Record<string,{title:string;kind:string;description:string;reference:string}>={
  solar:{title:'Atmósfera solar · recreación',kind:'ILUSTRACIÓN',description:'Superficie continua de plasma, filamentos y granulación inspirada en imágenes solares. Recreación visual en toda la esfera; no es una reconstrucción del campo magnético.',reference:'Campo firmado'},
  magnetogram:{title:'Campo magnético firmado',kind:'OBSERVACIÓN PROCESADA',description:'Blanco: positivo. Negro: negativo. Gris: alrededor de cero. Matriz completa en un plano, sin proyección sobre el Sol.',reference:'Campo firmado'},
  bplus:{title:'Polaridad positiva · B+',kind:'DERIVADO OBSERVACIONAL',description:'B+ = max(x, 0). Blanco indica mayor magnitud positiva; negro indica cero. Escala lineal normalizada.',reference:'Canal B+'},
  bminus:{title:'Polaridad negativa · |B−|',kind:'DERIVADO OBSERVACIONAL',description:'|B−| = max(−x, 0). Blanco indica mayor magnitud negativa; el canal conserva valores no negativos.',reference:'Magnitud B−'},
};
if(isTemporal)modes.solar={title:'Actividad magnética · recreación 3D',kind:'RECREACIÓN GUIADA POR HMI',description:'Ámbar: B+ · coral: B− · núcleos oscuros: concentraciones magnéticas recreadas, no manchas confirmadas. Proyección geométrica aproximada del disco; dorso ilustrativo sin observación HMI.',reference:'Campo firmado'};
function showLayer(name:string){
  layer=checkedLayer(name);const mode=modes[layer];
  if(context){for(const item of ['solar','magnetogram','bplus','bminus']){const go=context.scene.getObjectByName(item==='solar'?'SolarIllustration':'Layer_'+item);if(go)setActive(go,item===layer);}}
  $('layer-title').textContent=mode.title;$('view-kind').textContent=mode.kind;$('layer-description').textContent=mode.description;$('reference-name').textContent=mode.reference;
  for(const button of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-layer]')))button.setAttribute('aria-pressed',String(button.dataset.layer===layer));
  const ref=layer==='solar'?'magnetogram':layer;
  const image=$<HTMLImageElement>('reference-image');image.src=verifiedUrls.get(ref)??'';image.alt=mode.reference+'; fila 0 arriba, columnas conservadas';
  const signed=ref==='magnetogram';$('legend-min').textContent=signed?'−1 · B−':'0';$('legend-mid').textContent=signed?'0':'0,5';$('legend-max').textContent=signed?'+1 · B+':'1 · magnitud';
  const arImage=document.getElementById('ar-reference') as HTMLImageElement|null;if(arImage)arImage.src=verifiedUrls.get(ref)??'';
  const arNote=document.getElementById('ar-layer-note');if(arNote)arNote.textContent=mode.kind+' · '+mode.title+(signed?' · negro −1 / gris 0 / blanco +1':' · negro 0 / blanco 1');
  $('scene-side').textContent=layer==='solar'?(isTemporal?'FRENTE: HMI PROYECTADO · DORSO: RECREACIÓN':'RECREACIÓN 360°'):'REFERENCIA 2D';
  $('display-tools').hidden=layer==='solar';$('plasma').hidden=layer!=='solar';const surfaceReset=document.getElementById('surface-reset');if(surfaceReset)surfaceReset.hidden=layer!=='solar';
  surfaceClock.sync(performance.now());updateDisplay();diag.layer=layer;record('layer:'+layer);
}
function updateDisplay(){
  if(visual)visual.gain.value=displayGain;
  const signed=layer==='solar'||layer==='magnetogram', g=layer==='solar'?1:displayGain;
  const limit=(1/g).toLocaleString('es-CL',{maximumFractionDigits:3});
  $('reference-image').style.filter=signed?`contrast(${g})`:`brightness(${g})`;
  const arImage=document.getElementById('ar-reference');if(arImage)arImage.style.filter=$('reference-image').style.filter;
  $('legend-min').textContent=signed?'−'+limit+' · B−':'0';
  $('legend-mid').textContent=signed?'0':(0.5/g).toLocaleString('es-CL',{maximumFractionDigits:3});
  $('legend-max').textContent=signed?'+'+limit+' · B+':limit+' · magnitud';
  const note=g===1?'Escala original lineal.':'Contraste ×'+g+' · saturación visual en '+(signed?'±':'')+limit+'. Datos y SI intactos.';
  $('display-note').textContent=note;
  const arNote=document.getElementById('ar-layer-note');if(arNote)arNote.textContent=layer==='solar'&&isTemporal?'B+ ámbar · B− coral · regiones recreadas, no manchas confirmadas. Dorso sin HMI.':modes[layer].title+' · '+(signed?'negro −'+limit+' / blanco +'+limit:'negro 0 / blanco '+limit)+' · '+note;
  diag.displayGain=g;diag.illustrativeMotion=plasma;
}
$('contrast').onchange=e=>{displayGain=Number((e.target as HTMLSelectElement).value);if(![1,4,12].includes(displayGain))displayGain=1;updateDisplay();};
function plasmaButton(){
  for(const b of Array.from(document.querySelectorAll<HTMLElement>('#plasma,[data-surface-toggle]'))){b.setAttribute('aria-pressed',String(plasma));b.textContent=isTemporal?(plasma?'Pausar superficie':'Animar superficie'):(plasma?'Pausar plasma':'Animar plasma');}
}
function toggleSurface(){plasma=!plasma;surfaceClock.running=plasma;surfaceClock.sync(performance.now());plasmaButton();diag.illustrativeMotion=plasma;record('surface:'+plasma);}
function resetSurface(){surfaceClock.reset(performance.now());plasma=false;visualTime=0;if(visual)visual.time.value=0;plasmaButton();record('surface-reset');}
$('plasma').onclick=toggleSurface;plasmaButton();
const surfaceReset=document.getElementById('surface-reset');if(surfaceReset)surfaceReset.onclick=resetSurface;
for(const button of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-layer]')))button.onclick=()=>showLayer(button.dataset.layer!);
function setScale(value:number){scale=clampScale(value);object?.scale.setScalar(scale);$('scale-value').textContent=scale.toFixed(1).replace('.',',')+'×';diag.scale=scale;}
$('scale').oninput=e=>setScale(Number((e.target as HTMLInputElement).value));
function setAutomatic(value:boolean){automatic=value;if(orbit)orbit.autoRotate=value; $('auto').setAttribute('aria-pressed',String(value));$('auto').textContent=value?'Pausar giro':'Giro automático';diag.autoRotate=value;}
$('auto').onclick=()=>setAutomatic(!automatic);
function reset(){
  if(!context||!object||!orbit)return;
  setAutomatic(false);setScale(1);$<HTMLInputElement>('scale').value='1';
  object.rotation.set(0,0,0);
  if(!context.renderer.xr.isPresenting){
    orbit.controls?.reset();context.mainCamera.position.copy(cameraOrigin);orbit.setLookTargetPosition(rootPosition,true);orbit.setCameraTargetPosition(cameraOrigin,true);
  }
  record('reset');
}
$('reset').onclick=reset;
function zoom(factor:number){if(!context||!orbit||context.renderer.xr.isPresenting)return;const delta=context.mainCamera.position.clone().sub(rootPosition);delta.setLength(Math.max(orbit.minZoom,Math.min(orbit.maxZoom,delta.length()*factor)));context.mainCamera.position.copy(rootPosition).add(delta);orbit.controls?.update();record('zoom');}
$('zoom-in').onclick=()=>zoom(.85);$('zoom-out').onclick=()=>zoom(1.18);
$('download').onclick=()=>{
  const result={...diag,timestampUtc:new Date().toISOString(),url:location.href,userAgent:navigator.userAgent,samples,events,human:{device:$<HTMLInputElement>('device').value,browser:$<HTMLInputElement>('browser').value,result:$<HTMLSelectElement>('outcome').value,observations:$<HTMLTextAreaElement>('observations').value},note:'Human fields are user reports. Automated capability, placement events and desktop rendering do not certify physical mobile AR.'};
  const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=(isTemporal?'auralis-phase6-device-':'auralis-phase5-device-')+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
function fillScience(){
  const s=data.state;const note=document.getElementById('temporal-science-note');if(note)note.textContent='Estimación del SI actual; no pronóstico. '+(s.observation.split==='train'?'Observación de entrenamiento.':'Observación de validación utilizada en selección del modelo.')+' Esta secuencia no es una prueba temporal independiente.';
  const arState=document.getElementById('ar-state'),arSI=document.getElementById('ar-si');if(arState)arState.textContent=s.observation.time.record_utc.replace('.000Z',' UTC').replace('T',' ');if(arSI)arSI.textContent='SI '+s.observation.target_si.value.toFixed(6)+'% · ONNX '+s.coronium_results.prediction_si.toFixed(6)+'%';
  const date=new Date(s.observation.time.record_utc);
  $('header-date').textContent=new Intl.DateTimeFormat('es-CL',{dateStyle:'medium',timeZone:'UTC'}).format(date);
  $('state-date').textContent=new Intl.DateTimeFormat('es-CL',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(date);
  $('utc-time').textContent=s.observation.time.record_utc.slice(11,19)+' UTC';
  $('target-si').textContent=s.observation.target_si.value.toFixed(6).replace('.',',');
  $('prediction-si').textContent=s.coronium_results.prediction_si.toFixed(6).replace('.',',');
  $('delta-si').textContent=(s.coronium_results.prediction_si-s.observation.target_si.value).toFixed(6).replace('.',',')+' pp';
  $('model-name').textContent=data.model.name;
  const fields:Record<string,string>={'state-id':s.id,'observation-id':s.observation.id,filename:s.observation.magnetogram.filename,'tai-time':s.observation.time.record_tai+' TAI',protocol:s.coronium_results.protocol,'channel-means':s.derived.polarity.b_plus_mean.toFixed(9)+' / '+s.derived.polarity.b_minus_magnitude_mean.toFixed(9),region:'NOAA '+s.observation.region_context.noaa+' · HARP '+s.observation.region_context.harp+' (asociación de catálogo)'};
  for(const [id,value]of Object.entries(fields))$(id).textContent=value;
  Object.assign(diag,{stateId:s.id,observationId:s.observation.id,recordUTC:s.observation.time.record_utc,SI:s.observation.target_si.value,prediction:s.coronium_results.prediction_si,protocol:s.coronium_results.protocol,contractSha256:data.contract_sha256});
}
function createARPanel(){
  // Needle 5.1.12 explicitly supports direct children marked `ar` in its DOM
  // overlay, including reparenting in Needle Go. Do not depend on outside HTML.
  const panel=document.createElement('div');panel.className='ar phase5-ar';panel.style.display='none';
  panel.setAttribute('aria-label','Controles y referencia científica en AR');
  panel.innerHTML='<div class="ar-readout"><img id="ar-reference" width="64" height="64" alt="Referencia 2D, fila cero arriba"><div><strong id="ar-state"></strong><p id="ar-si"></p><small id="ar-layer-note"></small></div></div><div class="ar-buttons"></div><div class="ar-buttons ar-size"></div><small>Sol ilustrativo 360° · mapas observacionales de referencia 2D</small>';
  if(isTemporal)panel.querySelector(':scope > small')!.textContent='Frente: actividad HMI proyectada · dorso: recreación sin HMI';
  panel.querySelector('#ar-state')!.textContent=data.state.observation.time.record_utc.replace('.000Z',' UTC').replace('T',' ');
  panel.querySelector('#ar-si')!.textContent='SI '+data.state.observation.target_si.value.toFixed(6)+'% · ONNX '+data.state.coronium_results.prediction_si.toFixed(6)+'%';
  for(const [key,title]of Object.entries({solar:'Sol',magnetogram:'Magnetograma',bplus:'B+',bminus:'B−'})){const b=document.createElement('button');b.dataset.layer=key;b.textContent=title;b.onclick=()=>showLayer(key);panel.querySelector('.ar-buttons')!.append(b);}
  for(const [title,action]of [['Reducir',()=>setScale(scale-.1)],['Ampliar',()=>setScale(scale+.1)],['Escala 1×',()=>setScale(1)]] as const){const b=document.createElement('button');b.textContent=title;b.onclick=action;panel.querySelector('.ar-size')!.append(b);}
  const contrastButton=document.createElement('button');contrastButton.textContent='Contraste ×'+displayGain;contrastButton.onclick=()=>{displayGain=displayGain===1?4:displayGain===4?12:1;$<HTMLSelectElement>('contrast').value=String(displayGain);contrastButton.textContent='Contraste ×'+displayGain;updateDisplay();};panel.querySelector('.ar-size')!.append(contrastButton);
  if(isTemporal){
    const motion=document.createElement('div');motion.className='ar-buttons';
    const toggle=document.createElement('button');toggle.dataset.surfaceToggle='';toggle.onclick=toggleSurface;motion.append(toggle);
    const reset=document.createElement('button');reset.dataset.surfaceReset='';reset.textContent='Congelar en t=0';reset.onclick=resetSurface;motion.append(reset);panel.append(motion);
    const note=document.createElement('small');note.textContent='Movimiento ilustrativo; estados magnéticos basados en observaciones HMI';panel.append(note);
  }
  if(temporal){const timeline=document.createElement('div');timeline.className='temporal-ar';panel.append(timeline);temporal.bind(timeline,true);scientific?.bind(timeline,true);}
  panel.addEventListener('beforexrselect',event=>event.preventDefault());
  return panel;
}
function initialize(ctx:Context){
  if(released)return;context=ctx;
  object=ctx.scene.getObjectByName('SolarState');orbit=ctx.mainCamera.getComponent(OrbitControls)??undefined;
  if(!object||!orbit||!ctx.scene.getObjectByName('Phase5Placement')?.getComponent(WebARSessionRoot))throw new Error('La exportación no contiene la escena solar y sus controles Unity.');
  for(const name of ['SolarIllustration','Layer_magnetogram','Layer_bplus','Layer_bminus','IllustrativeSphere'])if(!ctx.scene.getObjectByName(name))throw new Error('Falta un recurso Unity: '+name);
  ctx.devicePixelRatio=Math.min(devicePixelRatio,1.5);
  object.traverse(o=>{if(o instanceof Mesh)for(const material of Array.isArray(o.material)?o.material:[o.material])material.toneMapped=false;});
  visual=polishMaterials(object,isTemporal);visualLast=performance.now();surfaceClock.sync(visualLast);plasmaButton();
  const visibility=new IntersectionObserver(entries=>{surfaceVisible=entries[0].isIntersecting;surfaceClock.sync(performance.now());});visibility.observe($('viewport'));cleanupCallbacks.push(()=>visibility.disconnect());
  cameraOrigin.copy(ctx.mainCamera.position);object.getWorldPosition(rootPosition);
  orbit.autoTarget=false;orbit.autoFit=false;orbit.enablePan=false;orbit.minZoom=1.15;orbit.maxZoom=3.8;orbit.autoRotateSpeed=.65;orbit.enableDamping=true;orbit.minPolarAngle=.12;orbit.maxPolarAngle=Math.PI-.12;orbit.setLookTargetPosition(rootPosition,true);
  const xr=ctx.scene.addComponent(WebXR,{createARButton:true,createVRButton:false,createSendToQuestButton:false,createQRCode:false,autoPlace:false,autoCenter:false,usePlacementReticle:true,usePlacementAdjustment:true,useQuicklookExport:false,useXRAnchor:true,arScale:1,defaultAvatar:false});void xr;
  const usdz=ctx.scene.addComponent(USDZExporter,{objectToExport:object,exportFileName:'auralis-phase5-'+data.state.id,interactive:false});
  if(ios){$('quicklook').hidden=false;$('quicklook').onclick=()=>{temporal?.pause();usdz.exportFileName='auralis-'+data.state.id;record('quicklook-request');void usdz.exportAndOpen().catch(fail);};}
  removePlaced=WebARSessionRoot.onPlaced(args=>{if(args.instance.context!==ctx)return;diag.placementCount=Number(diag.placementCount)+1;record('placed');$('placement').textContent='Colocación notificada. Comprueba visualmente escala, capas y estabilidad.';startSample();});
  let removeXRVisibility:(()=>void)|undefined;
  const sessionStart=()=>{
    const session=ctx.renderer.xr.getSession();const sync=()=>surfaceClock.sync(performance.now());
    session?.addEventListener('visibilitychange',sync);removeXRVisibility=()=>session?.removeEventListener('visibilitychange',sync);
    surfaceClock.sync(performance.now());setAutomatic(false);temporal?.pause();if(sample)stopSample('interrupted-session-start');record('session-start');$('placement').textContent='Sesión XR iniciada. Busca una superficie y toca para colocar.';};
  const sessionEnd=()=>{removeXRVisibility?.();removeXRVisibility=undefined;surfaceClock.sync(performance.now());temporal?.pause();if(sample)stopSample('interrupted-session-end');record('session-end');$('placement').textContent='Sesión finalizada. Continúa en 3D.';};
  ctx.renderer.xr.addEventListener('sessionstart',sessionStart);ctx.renderer.xr.addEventListener('sessionend',sessionEnd);
  cleanupCallbacks.push(()=>{removeXRVisibility?.();ctx.renderer.xr.removeEventListener('sessionstart',sessionStart);ctx.renderer.xr.removeEventListener('sessionend',sessionEnd);});
  ctx.pre_render_callbacks.push(()=>{const now=performance.now();if(isTemporal)visualTime=surfaceClock.tick(now,!document.hidden&&layer==='solar'&&(ctx.renderer.xr.isPresenting||surfaceVisible)&&(!ctx.renderer.xr.isPresenting||ctx.renderer.xr.getSession()?.visibilityState==='visible'));else if(plasma&&layer==='solar')visualTime+=Math.min((now-visualLast)/1000,.1);visualLast=now;if(visual)visual.time.value=visualTime;});
  ctx.post_render_callbacks.push(()=>{
    const now=performance.now(),info=ctx.renderer.info;
    if(sample&&lastFrame!==info.render.frame){const mode=ctx.renderer.xr.isPresenting?'xr':'web3d';if(mode!==sample.mode)stopSample('interrupted-mode-change');else if(info.render.calls>0)sample.times.push(now);}lastFrame=info.render.frame;
    if(now-lastStats>500){lastStats=now;Object.assign(diag,{status:'ready',layer,scale,autoRotate:automatic,illustrativeTime:visualTime,illustrativeMotion:plasma,...(isTemporal?{surfaceSeed:SURFACE_SEED,surfaceVisible,surfaceGuideState:data.state.id,surfaceGuideMaps:[visual?.guidePlus.value?.name,visual?.guideMinus.value?.name],surfaceShader:visual?.guidePlus.value?'anchored-hmi-v71':null}:{}),drawCalls:info.render.calls,triangles:info.render.triangles,renderFrames:info.render.frame,gpuTextures:info.memory.textures,gpuGeometries:info.memory.geometries,retainedEvents:events.length,pixelRatio:ctx.renderer.getPixelRatio(),cameraPosition:ctx.mainCamera.position.toArray(),cameraDistance:ctx.mainCamera.position.distanceTo(rootPosition),orbitEnabled:!!orbit?.controls?.enabled,canvasAttached:ctx.renderer.domElement.isConnected,engineElements:document.querySelectorAll('needle-engine').length});$('diagnostics').textContent=JSON.stringify(diag,null,2);}
  });
  temporal?.activate();scientific?.setEnabled(true);if(temporal&&visual){const texture=temporal.bundles[temporal.index].textures.get('solar')!;visual.solarFrom.value=texture;visual.solarTo.value=texture;}showLayer(layer);setScale(scale);setAutomatic(false);buttons(true);diag.source='unity-glb-loaded';diag.readyMs=Math.round(performance.now()-started);diag.exportHashVerified=true;diag.exportEvidence=evidence;
  $('load-status').textContent='Unity → Needle · escena y recursos verificados';clearTimeout(timer);$('retry').hidden=true;record('ready');
}
function release(){
  if(sample)stopSample('interrupted-release');attempt++;released=true;setAutomatic(false);clearTimeout(timer);removePlaced?.();removePlaced=undefined;
  for(const fn of cleanupCallbacks.splice(0))fn();
  scientific?.setEnabled(false);scientific?.dispose();scientific=undefined;temporal?.dispose(new Set(verifiedUrls.values()));temporal=undefined;context?.dispose();element?.remove();if(sceneUrl){URL.revokeObjectURL(sceneUrl);sceneUrl=undefined;}element=undefined;context=undefined;object=undefined;orbit=undefined;visual=undefined;buttons(false);
  $('retry').hidden=false;$('load-status').textContent='Visor liberado. La referencia 2D sigue disponible.';diag.status='disposed';diag.engineElements=document.querySelectorAll('needle-engine').length;diag.canvasAttached=false;diag.callbacksReleased=true;$('diagnostics').textContent=JSON.stringify(diag,null,2);record('released');
}
$('release').onclick=release;
listen(window,'pagehide',()=>{release();for(const url of verifiedUrls.values())URL.revokeObjectURL(url);verifiedUrls.clear();abort.abort();});
async function get(path:string){const response=await fetch(new URL(path,location.href),{signal:AbortSignal.any([abort.signal,AbortSignal.timeout(25000)])});if(!response.ok)throw new Error('Recurso no disponible: '+path);return response.arrayBuffer();}
async function mount(){
  if(loading)return;const currentAttempt=++attempt;loading=true;released=false;started=performance.now();diag.errors=[];$('retry').hidden=true;$('load-status').textContent='Verificando datos y exportación Unity…';
  try{
    const [stateBytes,metaBytes]=await Promise.all([get(assetBase+'state.json'),get(assetBase+'export-evidence.json')]);
    data=validateState(JSON.parse(new TextDecoder().decode(stateBytes)));evidence=JSON.parse(new TextDecoder().decode(metaBytes));
    if(await digest(stateBytes)!==evidence.stateSha256)throw new Error('Los datos y la evidencia Unity no coinciden.');
    if(isTemporal){
      for(const url of verifiedUrls.values())URL.revokeObjectURL(url);verifiedUrls.clear();
      const baseData=data;
      temporal=new TemporalSequence({
        commit:bundle=>{
          data={...baseData,state:bundle.entry.state,layers:bundle.entry.layers};
          verifiedUrls.clear();for(const [k,u]of bundle.urls)verifiedUrls.set(k,u);
          if(context)for(const [key,texture]of bundle.textures){
            const mesh=context.scene.getObjectByName(key==='solar'?'IllustrativeSphere':'Layer_'+key) as Mesh;
            const mat=(Array.isArray(mesh.material)?mesh.material[0]:mesh.material) as any;
            const old=mat.map;mat.map=texture;mat.needsUpdate=true;
            if(old&&!temporal?.bundles.some(b=>Array.from(b.textures.values()).includes(old)))old.dispose();
          }
          if(visual){visual.guidePlus.value=bundle.textures.get('bplus')!;visual.guideMinus.value=bundle.textures.get('bminus')!;visual.guideDisk.value.set(bundle.activity.disk.cx,bundle.activity.disk.cy,bundle.activity.disk.radius);}
          Object.assign(diag,{surfaceGuideState:bundle.entry.state.id,surfaceGuideMaps:[bundle.textures.get('bplus')!.name,bundle.textures.get('bminus')!.name],activeMaps:Object.fromEntries(Array.from(bundle.textures,([key,texture])=>[key,{name:texture.name,sha256:(key==='solar'?bundle.activity.solar:bundle.entry.layers[key]).sha256,flipY:texture.flipY}])),solarActivity:{id:bundle.activity.id,sha256:bundle.activity.solar.sha256,sourceSha256:bundle.activity.source_sha256,disk:bundle.activity.disk},magnetogramFile:bundle.entry.state.observation.magnetogram.filename});
          fillScience();scientific?.setState(data.state.id);showLayer(layer);record('state:'+data.state.id);
        },
        transition:(from,to,t)=>{if(visual){visual.solarFrom.value=from.textures.get('solar')!;visual.solarTo.value=to.textures.get('solar')!;visual.solarMix.value=t;}Object.assign(diag,{solarFrom:from.entry.state.id,solarTo:to.entry.state.id,solarMix:t});},
        fade:value=>{if(visual)visual.fade.value=value;$('reference-image').style.opacity=String(value);const arImage=document.getElementById('ar-reference');if(arImage)arImage.style.opacity=String(value);},
        status:state=>{Object.assign(diag,state);$('diagnostics').textContent=JSON.stringify(diag,null,2);}
      });
      const temporalEvidence=await temporal.load();
      if(temporalEvidence.unity_glb_sha256!==evidence.sha256||temporalEvidence.contract_sha256!==baseData.contract_sha256)throw Error('La secuencia no corresponde a la escena y al contrato verificados.');
      const [contextBytes,contextEvidence]=await Promise.all([get('/phase7/context.json'),get('/phase7/context-evidence.json')]);
      const contextHash=await digest(contextBytes);
      if(contextHash!==JSON.parse(new TextDecoder().decode(contextEvidence)).context_sha256)throw Error('Integridad del contexto científico incorrecta.');
      const historical=validateContext(JSON.parse(new TextDecoder().decode(contextBytes)),temporal.manifest,temporalEvidence.sequence_sha256);
      scientific=new ScientificContext(historical,{pause:()=>temporal?.pause(),selectState:(index:number)=>temporal?.select(index),status:(state:Record<string,unknown>)=>{Object.assign(diag,state);$('diagnostics').textContent=JSON.stringify(diag,null,2);}});
      Object.assign(diag,{historicalContextSha256:contextHash,historicalEventCount:historical.events.length});
      temporal.bind($('timeline'));scientific.bind($('timeline'));
    }else{
      for(const name of ['magnetogram','bplus','bminus']){const bytes=await get(data.layers[name].url);if(await digest(bytes)!==data.layers[name].sha256)throw new Error('Integridad incorrecta: '+name);const previous=verifiedUrls.get(name);if(previous)URL.revokeObjectURL(previous);verifiedUrls.set(name,URL.createObjectURL(new Blob([bytes],{type:'image/png'})));}
      fillScience();showLayer(layer);
    }
    const glbBytes=await get(assetBase+'Phase5Solar.glb');await verifyExport(glbBytes,evidence,stateBytes);
    if(currentAttempt!==attempt)return;
    Object.assign(Context.DefaultWebGLRendererParameters,{alpha:true,antialias:true});
    sceneUrl=URL.createObjectURL(new Blob([glbBytes],{type:'model/gltf-binary'}));
    element=document.createElement('needle-engine');element.setAttribute('camera-controls','true');element.setAttribute('loading-background','transparent');element.setAttribute('src',sceneUrl);element.append(createARPanel());
    element.addEventListener('loadfinished',e=>{const ctx=(e as CustomEvent<{context:Context}>).detail.context;if(currentAttempt!==attempt){ctx.dispose();return;}try{initialize(ctx);}catch(error){release();fail(error);}});
    element.addEventListener('loaderror',()=>{release();fail('No se pudo cargar la escena Unity. La referencia 2D sigue disponible.');});
    $('viewport').append(element);timer=setTimeout(()=>{if(diag.source!=='unity-glb-loaded'){release();fail('La escena no terminó de cargar. Revisa conexión y WebGL y reintenta.');}},30000);
  }catch(error){scientific?.setEnabled(false);scientific?.dispose();scientific=undefined;temporal?.dispose(new Set(verifiedUrls.values()));temporal=undefined;fail(error);}finally{loading=false;}
}
$('retry').onclick=()=>{release();diag.source='waiting-for-real-unity';void mount();};
void mount();
void (async()=>{let supported=false,error=false;try{supported=!!await navigator.xr?.isSessionSupported('immersive-ar');}catch{error=true;}Object.assign(diag,{immersiveAR:supported,secureContext:isSecureContext});$('capability').textContent=describeAR({secure:isSecureContext,immersiveAR:supported,ios,error});})();
const shareUrl=new URL(location.href);shareUrl.search='';shareUrl.hash='';
$<HTMLAnchorElement>('share-url').href=shareUrl.href;$('share-url').textContent=shareUrl.href;
$('share-note').textContent=shareable(shareUrl.href)?(isTemporal?'Secuencia de cinco observaciones. Prueba física pendiente.':'URL pública del primer estado. Prueba física pendiente.'):'Vista local: este QR no abre el Mac desde tu teléfono.';
if(shareable(shareUrl.href)){const url=new URL('https://appclip.needle.tools/ar');url.searchParams.set('url',shareUrl.href);$<HTMLAnchorElement>('ios-launch').href=url.href;$('ios-launch').hidden=false;}
void QRCode.toCanvas($<HTMLCanvasElement>('qr'),shareUrl.href,{width:200,margin:2,errorCorrectionLevel:'M'}).catch(fail);
