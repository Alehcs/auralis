import './style.css';
import QRCode from 'qrcode';
import { BoxGeometry, Color, DirectionalLight, Group, HemisphereLight, Mesh, MeshStandardMaterial, Object3D, PerspectiveCamera, Vector3 } from 'three';
import { Camera, Context, OrbitControls, WebXR, WebARSessionRoot, USDZExporter } from '@needle-tools/engine';
import { summarizeFrames } from './render-sample.mjs';
import { describeAR, shareable } from './capabilities.mjs';

const $ = <T extends HTMLElement = HTMLElement>(id:string) => document.getElementById(id) as T;
const params = new URLSearchParams(location.search);
const unity = params.get('scene') !== 'provisional';
const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const diagnostic: Record<string, unknown> = {timestamp:new Date().toISOString(),url:location.href,userAgent:navigator.userAgent,engine:'5.1.12',build:'phase4.2-20260909-b',source:unity?'unity-export-requested':'typescript-provisional',unityEditorExecuted:unity?null:false,secureContext:isSecureContext,immersiveAR:null,placementCount:0,errors:[]};
let ctx:Context|undefined;
const samples:Record<string,unknown>[]=[];
const events:Record<string,unknown>[]=[];
let sample:{start:number;mode:string;times:number[];timer:ReturnType<typeof setTimeout>}|undefined;
let lastRenderFrame=-1;
function event(type:string){events.push({type,elapsedMs:Math.round(performance.now())});}
function finishSample(reason='completed'){
  if(!sample)return;
  const current=sample;sample=undefined;clearTimeout(current.timer);
  const result={mode:current.mode,status:reason,...summarizeFrames(current.times,performance.now()-current.start),source:diagnostic.source};
  samples.push(result);
  $('sample-result').textContent=JSON.stringify(result,null,2);
  ($('sample') as HTMLButtonElement).disabled=false;
}
function startSample(){
  if(!ctx||!readyAt)return;
  if(sample)finishSample('restarted');
  sample={start:performance.now(),mode:ctx.renderer.xr.isPresenting?'xr':'web3d',times:[],timer:setTimeout(()=>finishSample(),30000)};
  ($('sample') as HTMLButtonElement).disabled=true;
  $('sample-result').textContent='Midiendo 30 s. Mantén el cubo visible y mueve la cámara lentamente.';
  if(!ctx.renderer.xr.isPresenting)$('viewport').scrollIntoView({block:'center',behavior:'smooth'});
}
$('sample').onclick=startSample;
document.addEventListener('visibilitychange',()=>{event('visibility:'+document.visibilityState);if(document.hidden&&sample&&!ctx?.renderer.xr.isPresenting)finishSample('interrupted-hidden');});

let object:Object3D|undefined;
let baseScale = new Vector3(1,1,1);
let tint=0;
const originalColors=new Map<MeshStandardMaterial,Color>();
const colors=[0x47d5c1,0xf5a44a,0x91a8ff];
let readyAt=0,previous=0,lastStats=0;
const intervals:number[]=[];
function fail(error:unknown){const message=error instanceof Error?error.message:String(error);(diagnostic.errors as string[]).push(message);$('load-status').textContent='No se pudo completar la prueba: '+message;}
window.addEventListener('error',e=>fail(e.message));
window.addEventListener('unhandledrejection',e=>fail(e.reason));
$('provenance').textContent=unity?'Modo Unity: exige public/unity/Phase4Probe.glb. Si falta o falla, no se sustituye.':'Escena provisional creada en TypeScript dentro de Needle. No acredita exportación desde Unity.';

function changeColor(){tint=(tint+1)%colors.length;object?.traverse(o=>{if(o instanceof Mesh){for(const material of Array.isArray(o.material)?o.material:[o.material]){if('color' in material) (material as MeshStandardMaterial).color.setHex(colors[tint]);}}});diagnostic.colorIndex=tint;}
function setScale(value:number){object?.scale.copy(baseScale).multiplyScalar(value);$('scale-value').textContent=value.toFixed(1)+'×';diagnostic.objectScale=value;}
$('color').onclick=changeColor;
$('rotate').onclick=()=>{if(object){object.rotation.y+=Math.PI/4;diagnostic.rotationY=object.rotation.y;}};
$('scale').oninput=e=>setScale(Number((e.target as HTMLInputElement).value));
$('reset').onclick=()=>{if(object){object.rotation.set(0,0,0);setScale(1);($('scale') as HTMLInputElement).value='1';tint=0;for(const [material,color] of originalColors)material.color.copy(color);diagnostic.colorIndex=0;diagnostic.rotationY=0;}};
$('download').onclick=()=>{const blob=new Blob([JSON.stringify({...diagnostic,timestamp:new Date().toISOString(),samples,events,human:{device:($('device') as HTMLInputElement).value,network:($('network') as HTMLInputElement).value,observations:($('observations') as HTMLTextAreaElement).value},resourceTiming:performance.getEntriesByType('resource').map(entry=>{const r=entry as PerformanceResourceTiming;return {name:r.name,durationMs:r.duration,transferSize:r.transferSize,encodedBodySize:r.encodedBodySize};}),resourceTimingNote:'Zero sizes may mean cache or unavailable cross-origin timing. Not a mobile cold-load claim.'},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='auralis-phase41-device-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};

async function capabilities(){let supported=false,error=false;try{supported=!!(await navigator.xr?.isSessionSupported('immersive-ar'));}catch{error=true;}diagnostic.immersiveAR=supported;diagnostic.capabilityError=error;$('capability').textContent=describeAR({secure:isSecureContext,immersiveAR:supported,ios,error});}
void capabilities();
const shareUrl=new URL(location.href);shareUrl.hash='';
$('share-url').textContent=shareUrl.href;($('share-url') as HTMLAnchorElement).href=shareUrl.href;
$('share-note').textContent=shareable(shareUrl.href)?'El QR abre esta URL. Para Needle Go, debe ser pública y accesible sin iniciar sesión.':'URL local: este QR no abre el Mac desde otro teléfono. Publica por HTTPS antes de probar AR móvil.';
const iosLaunch=new URL('https://appclip.needle.tools/ar');iosLaunch.searchParams.set('url',shareUrl.href);if(shareable(shareUrl.href))($('ios-launch') as HTMLAnchorElement).href=iosLaunch.href;
void QRCode.toCanvas($('qr') as HTMLCanvasElement,shareUrl.href,{width:220,margin:2,errorCorrectionLevel:'M'}).catch(fail);

Object.assign(Context.DefaultWebGLRendererParameters,{alpha:true,antialias:true});
function initializeScene(context:Context){
  if(readyAt)return;
  ctx=context;
  object=unity?context.scene.getObjectByName('ProbeObject'):undefined;
  if(unity&&!object){fail('Falta una exportación Unity válida con ProbeObject. Ejecuta la exportación en el editor.');return;}
  if(!unity){
    const root=new Group();root.name='PlacementRoot';context.scene.add(root);
    const cube=new Mesh(new BoxGeometry(.2,.2,.2),new MeshStandardMaterial({color:colors[0],roughness:.4,metalness:.1}));
    cube.position.y=.1;
    object=new Group();object.name='ProbeObject';object.add(cube);root.add(object);
    root.addComponent(WebARSessionRoot,{autoPlace:false,autoCenter:false,arScale:1,arTouchTransform:true,useXRAnchor:true});
    context.scene.add(new HemisphereLight(0xeaf5ff,0x48647b,2));
    const light=new DirectionalLight(0xffffff,3);light.position.set(2,4,3);context.scene.add(light);
    const camera=new PerspectiveCamera(45,1,.01,30);camera.position.set(.5,.4,.7);camera.lookAt(0,.1,0);context.scene.add(camera);context.mainCamera=camera;
    // Needle OrbitControls requires the active Needle Camera component.
    context.setCurrentCamera(camera.addComponent(Camera,{nearClipPlane:.01,farClipPlane:30}));
    const orbit=camera.addComponent(OrbitControls,{autoTarget:false,autoFit:false});orbit.setLookTargetPosition(new Vector3(0,.1,0),true);
  }
  baseScale=object!.scale.clone();
  object!.traverse(o=>{if(o instanceof Mesh)for(const material of Array.isArray(o.material)?o.material:[o.material])if('color' in material)originalColors.set(material as MeshStandardMaterial,(material as MeshStandardMaterial).color.clone());});
  diagnostic.arRootPresent=!!context.scene.getObjectByName('PlacementRoot')?.getComponent(WebARSessionRoot);
  diagnostic.unityEditorExecuted=unity&&diagnostic.exportHashVerified===true;
  context.devicePixelRatio=Math.min(devicePixelRatio,1.5);
  context.post_render_callbacks.push(()=>{const info=context.renderer.info; if(sample&&info.render.frame!==lastRenderFrame){const mode=context.renderer.xr.isPresenting?'xr':'web3d';if(mode!==sample.mode)finishSample('interrupted-mode-change');else if(info.render.calls>0)sample.times.push(performance.now());}lastRenderFrame=info.render.frame; if(info.render.calls>0) Object.assign(diagnostic,{drawCalls:info.render.calls,triangles:info.render.triangles,renderFrames:info.render.frame});});
  // Shared web layer; Unity authors placement root, camera, mesh and lighting.
  const xr=context.scene.addComponent(WebXR,{createARButton:true,createVRButton:false,createSendToQuestButton:false,createQRCode:false,autoPlace:false,autoCenter:false,usePlacementReticle:true,usePlacementAdjustment:true,useQuicklookExport:false,useXRAnchor:true,arScale:1,defaultAvatar:false});
  void xr;
  const usdz=context.scene.addComponent(USDZExporter,{objectToExport:object,exportFileName:'auralis-phase4-cube',interactive:false});
  if(ios){$('quicklook').hidden=false;$('quicklook').onclick=()=>{void usdz.exportAndOpen().catch(fail);};}
  WebARSessionRoot.onPlaced(()=>{event('placed');if(!sample||sample.mode!=='xr')startSample();diagnostic.placementCount=Number(diagnostic.placementCount)+1;$('placement').textContent='Needle notificó la colocación. Comprueba visualmente escala y estabilidad.';});
  context.renderer.xr.addEventListener('sessionstart',()=>{event('sessionstart');if(sample)finishSample('interrupted-session-start');diagnostic.sessionStarted=true;$('placement').textContent='Sesión XR iniciada. Busca una superficie y toca la retícula.';});
  context.renderer.xr.addEventListener('sessionend',()=>{event('sessionend');if(sample)finishSample('interrupted-session-end');diagnostic.sessionEnded=true;$('placement').textContent='Sesión finalizada. Modo 3D disponible.';});
  readyAt=performance.now();diagnostic.readyMs=Math.round(readyAt);diagnostic.source=unity?'unity-glb-loaded':'typescript-provisional';
  for(const id of ['color','rotate','scale','reset','sample']) ($<HTMLButtonElement>(id)).disabled=false;
  $('load-status').textContent=unity?'Escena real Unity 6.3 → Needle 5.1.12 · GLB verificado':'Needle 5.1.12 ejecutándose · escena provisional TypeScript';
}

const element=document.createElement('needle-engine');element.setAttribute('camera-controls','true');element.setAttribute('loading-background','transparent');
// Loading completes even when the viewer is outside the viewport after reload.
element.addEventListener('loadfinished',event=>initializeScene((event as CustomEvent<{context:Context}>).detail.context));
if(unity){$('scene-warning').textContent='Modo Unity: carga únicamente el GLB real con su evidencia de exportación.';}else{$('scene-warning').textContent='Escena provisional TypeScript: no es la exportación Unity.';document.querySelector('footer')!.textContent='Escena provisional TypeScript · Sin datos solares';}
if(unity) element.setAttribute('src','./unity/Phase4Probe.glb');
element.addEventListener('loaderror',()=>fail('Error al cargar el GLB solicitado.'));
async function mountScene(){
  if(unity){
    try{
      const [modelResponse,metaResponse]=await Promise.all([fetch('./unity/Phase4Probe.glb'),fetch('./unity/export-evidence.json')]);
      if(!modelResponse.ok||!metaResponse.ok)throw new Error('No existe el GLB real o su evidencia Unity. Exporta primero en el editor.');
      const data=await modelResponse.arrayBuffer();
      if(new TextDecoder().decode(data.slice(0,4))!=='glTF')throw new Error('No existe un GLB Unity válido en esta publicación.');
      const meta=await metaResponse.json();
      const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),b=>b.toString(16).padStart(2,'0')).join('');
      if(new TextDecoder().decode(data.slice(0,4))!=='glTF'||sha!==meta.sha256||data.byteLength!==meta.bytes||meta.exporterVersion!=='5.1.12')throw new Error('GLB/evidencia Unity no coinciden.');
      diagnostic.exportEvidence=meta;
      diagnostic.exportHashVerified=true;
    }catch(error){fail(error);return;}
  }
  $('viewport').append(element);
}
void mountScene();
element.addEventListener('pointerdown',()=>{diagnostic.pointerDowns=Number(diagnostic.pointerDowns??0)+1;});
setTimeout(()=>{if(!readyAt&&!(diagnostic.errors as string[]).length)fail('El motor no terminó de cargar en 30 s; revisa WebGL, red o el GLB.');},30000);
function measure(now:number){
  if(ctx&&readyAt&&document.visibilityState==='visible'){
    if(previous&&now-readyAt>2000){intervals.push(now-previous);if(intervals.length>600)intervals.shift();}
    previous=now;
    if(now-lastStats>1000){lastStats=now;const sorted=[...intervals].sort((a,b)=>a-b);const median=sorted[Math.floor(sorted.length*.5)];const p95=sorted[Math.floor(sorted.length*.95)];
      Object.assign(diagnostic,{rafSamples:sorted.length,rafMedianMs:median?+median.toFixed(2):null,rafP95Ms:p95?+p95.toFixed(2):null,pixelRatio:ctx.renderer.getPixelRatio(),placementCount:diagnostic.placementCount});
      $('metrics').textContent=JSON.stringify({source:diagnostic.source,build:diagnostic.build,unityEditorExecuted:diagnostic.unityEditorExecuted,exportHashVerified:diagnostic.exportHashVerified,exportEvidence:diagnostic.exportEvidence,arRootPresent:diagnostic.arRootPresent,readyMs:diagnostic.readyMs,rafSamples:diagnostic.rafSamples,rafMedianMs:diagnostic.rafMedianMs,rafP95Ms:diagnostic.rafP95Ms,drawCalls:diagnostic.drawCalls,triangles:diagnostic.triangles,pixelRatio:diagnostic.pixelRatio,immersiveAR:diagnostic.immersiveAR,placementCount:diagnostic.placementCount,cameraPosition:ctx.mainCamera.position.toArray(),orbitEnabled:ctx.mainCamera.getComponent(OrbitControls)?.enabled,orbitConnected:!!ctx.mainCamera.getComponent(OrbitControls)?.controls,orbitInputEnabled:ctx.mainCamera.getComponent(OrbitControls)?.controls?.enabled,needleCameraActive:ctx.mainCamera.getComponent(Camera)===ctx.mainCameraComponent,pointerDowns:diagnostic.pointerDowns??0,colorIndex:tint,objectScale:diagnostic.objectScale??1,rotationY:diagnostic.rotationY??0},null,2);
    }
  }else previous=0;
  requestAnimationFrame(measure);
}
requestAnimationFrame(measure);

// Optional agent interface uses the same scale action as the visible slider.
const modelContext=(document as Document & {modelContext?:{registerTool:(tool:unknown,options?:{signal:AbortSignal})=>unknown}}).modelContext;
if(modelContext?.registerTool){
  const lifecycle=new AbortController();
  window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
  try{Promise.resolve(modelContext.registerTool({name:'set_probe_scale',description:'Change the test cube scale (0.5 to 2), using the visible scale control.',inputSchema:{type:'object',properties:{scale:{type:'number',minimum:.5,maximum:2}},required:['scale'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input:unknown){
    const value=(input as {scale?:unknown})?.scale;
    if(typeof value!=='number'||!Number.isFinite(value)||value<.5||value>2||Object.keys(input as object).some(k=>k!=='scale'))throw new Error('Expected only scale between 0.5 and 2.');
    if(!object)throw new Error('Scene not ready.');
    const rounded=Math.round(value*10)/10;setScale(rounded);($('scale') as HTMLInputElement).value=String(rounded);return {scale:rounded,source:diagnostic.source};
  }},{signal:lifecycle.signal})).catch(error=>console.warn('Optional WebMCP unavailable',error));}catch(error){console.warn('Optional WebMCP unavailable',error);}
}
