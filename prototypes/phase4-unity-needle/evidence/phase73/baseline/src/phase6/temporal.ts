import {Texture,SRGBColorSpace,LinearMipmapLinearFilter,LinearFilter} from 'three';
import {digest} from '../phase5/contract.mjs';
import {validateActivity} from './activity.mjs';
import {CHANNELS,validateSequence,nextIndex,timelinePositions} from './sequence.mjs';
import './timeline.css';
type Bundle={entry:any;activity:any;urls:Map<string,string>;textures:Map<string,Texture>};
type Hooks={commit:(b:Bundle)=>void;fade:(value:number)=>void;transition:(from:Bundle,to:Bundle,t:number)=>void;status:(s:Record<string,unknown>)=>void};
export class TemporalSequence{
  manifest:any; bundles:Bundle[]=[];index=0;target=0;direction=1;playing=false;ready=false;
  private timer:ReturnType<typeof setTimeout>|undefined;private frame=0;private disposed=false;private abort=new AbortController();private changes=0;
  constructor(private hooks:Hooks){}
  async load(){
    const fetchBytes=async(url:string)=>{const r=await fetch(url,{signal:AbortSignal.any([this.abort.signal,AbortSignal.timeout(25000)])});if(!r.ok)throw Error('No se pudo cargar '+url);return r.arrayBuffer();};
    try{
      const [bytes,evidenceBytes]=await Promise.all([fetchBytes('/phase6/sequence.json'),fetchBytes('/phase6/sequence-evidence.json')]);
      const evidence=JSON.parse(new TextDecoder().decode(evidenceBytes));
      if(await digest(bytes)!==evidence.sequence_sha256)throw Error('Integridad de la secuencia incorrecta.');
      this.manifest=validateSequence(JSON.parse(new TextDecoder().decode(bytes)));
      if(this.manifest.contract_sha256!==evidence.contract_sha256)throw Error('Procedencia temporal incorrecta.');
      const [activityBytes,activityEvidenceBytes]=await Promise.all([fetchBytes('/phase6/activity.json'),fetchBytes('/phase6/activity-evidence.json')]);
      if(await digest(activityBytes)!==JSON.parse(new TextDecoder().decode(activityEvidenceBytes)).activity_sha256)throw Error('Integridad de la actividad solar incorrecta.');
      const activity=validateActivity(JSON.parse(new TextDecoder().decode(activityBytes)),this.manifest,evidence.sequence_sha256,evidence.unity_glb_sha256);
      // Fixed 20-texture cache: 15 scientific maps and five baked solar states.
      // Serial work bounds concurrent decoding and makes cancellation deterministic.
      for(const [i,entry] of this.manifest.entries.entries()){
        const bundle:Bundle={entry,activity:activity.entries[i],urls:new Map(),textures:new Map()};this.bundles.push(bundle);
        for(const key of [...CHANNELS,'solar']){
          const asset=key==='solar'?bundle.activity.solar:entry.layers[key],b=await fetchBytes(asset.url);
          if(await digest(b)!==asset.sha256)throw Error('Integridad del mapa incorrecta: '+entry.state.id+' '+key);
          if(this.disposed)throw Error('Carga temporal cancelada.');
          const url=URL.createObjectURL(new Blob([b],{type:'image/png'}));bundle.urls.set(key,url);
          const image=new Image();image.src=url;await image.decode();
          if(this.disposed)throw Error('Carga temporal cancelada.');
          if(image.naturalWidth!==asset.width||image.naturalHeight!==asset.height)throw Error('Dimensiones del mapa incorrectas.');
          const texture=new Texture(image);texture.flipY=false;texture.colorSpace=SRGBColorSpace;texture.minFilter=LinearMipmapLinearFilter;texture.magFilter=LinearFilter;texture.needsUpdate=true;texture.name=entry.state.id+'/'+key;
          bundle.textures.set(key,texture);
        }
      }
      // Presentation hero only: preserve chronological order and every state.
      const hero=this.bundles.findIndex(b=>b.entry.state.id==='hmi-2022-03-29');
      if(hero<0)throw Error('El estado hero del 29 de marzo no está disponible.');
      this.index=hero;this.target=hero;
      this.hooks.commit(this.bundles[this.index]);return evidence;
    }catch(e){this.dispose();throw e;}
  }
  bind(container:HTMLElement,ar=false){
    container.innerHTML='<div class="time-actions"><button data-time="prev">Anterior</button><button data-time="play">Reproducir</button><button data-time="next">Siguiente</button><label>Dirección <select data-time="direction"><option value="1">Adelante</option><option value="-1">Atrás</option></select></label><strong data-time="position"></strong></div><div class="time-axis" role="group" aria-label="Observaciones históricas"></div><p class="time-note-real">Puntos: observaciones reales · 2 s por estado, no tiempo físico. El fundido es solo visual.</p>';
    const axis=container.querySelector('.time-axis') as HTMLElement,positions=timelinePositions(this.manifest.entries);
    this.manifest.entries.forEach((entry:any,i:number)=>{const b=document.createElement('button');b.dataset.stateIndex=String(i);b.style.setProperty('--position',positions[i]*100+'%');const d=new Date(entry.state.observation.time.record_utc);b.textContent=new Intl.DateTimeFormat('es-CL',{day:'numeric',month:'short',timeZone:'UTC'}).format(d);b.setAttribute('aria-label',(ar?'AR: ':'')+'Seleccionar '+d.toISOString().slice(0,10));axis.append(b);b.addEventListener('click',()=>this.select(i),{signal:this.abort.signal});});
    const on=(key:string,fn:()=>void)=>container.querySelector(`[data-time="${key}"]`)!.addEventListener('click',fn,{signal:this.abort.signal});
    on('prev',()=>this.select(nextIndex(this.target,-1)));on('next',()=>this.select(nextIndex(this.target,1)));on('play',()=>this.playing?this.pause():this.play());
    container.querySelector('select')!.addEventListener('change',e=>{const direction=Number((e.target as HTMLSelectElement).value);this.pause();this.direction=direction;this.update();},{signal:this.abort.signal});this.update();
  }
  activate(){this.ready=true;this.hooks.commit(this.bundles[this.index]);this.update();}
  private update(){
    for(const b of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-state-index]'))){b.disabled=!this.ready;b.setAttribute('aria-pressed',String(Number(b.dataset.stateIndex)===this.index));}
    for(const b of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-time="prev"]')))b.disabled=!this.ready||this.target===0;
    for(const b of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-time="next"]')))b.disabled=!this.ready||this.target===4;
    for(const b of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-time="play"]'))){b.disabled=!this.ready;b.textContent=this.playing?'Pausar secuencia':'Reproducir';b.setAttribute('aria-pressed',String(this.playing));}
    for(const el of Array.from(document.querySelectorAll<HTMLSelectElement>('[data-time="direction"]'))){el.disabled=!this.ready;el.value=String(this.direction);}
    for(const el of Array.from(document.querySelectorAll('[data-time="position"]')))el.textContent=`${this.index+1} / 5`;
    this.hooks.status({stateIndex:this.index,pendingStateIndex:this.target,playing:this.playing,playDirection:this.direction,transitioning:this.frame!==0,cachedTextures:this.bundles.reduce((n,b)=>n+b.textures.size,0),temporalChanges:this.changes});
  }
  pause(){this.playing=false;clearTimeout(this.timer);this.timer=undefined;cancelAnimationFrame(this.frame);this.frame=0;this.target=this.index;this.hooks.fade(1);if(this.bundles[this.index])this.hooks.transition(this.bundles[this.index],this.bundles[this.index],1);this.update();}
  play(){if(!this.ready||this.disposed)return;this.playing=true;if(this.index===(this.direction===1?4:0))this.select(this.direction===1?0:4,false);else this.schedule();this.update();}
  private schedule(){clearTimeout(this.timer);if(!this.playing)return;if(this.index===(this.direction===1?4:0)){this.playing=false;this.update();return;}this.timer=setTimeout(()=>this.select(nextIndex(this.index,this.direction),false),2000);}
  select(index:number,manual=true){
    if(!this.ready||this.disposed||!Number.isInteger(index)||index<0||index>4)return;
    if(manual)this.pause();else{clearTimeout(this.timer);cancelAnimationFrame(this.frame);this.frame=0;}
    this.target=index;if(index===this.index){this.schedule();this.update();return;}
    const duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:260,start=performance.now(),from=this.bundles[this.index],to=this.bundles[index];let committed=false;
    const tick=(now:number)=>{
      if(this.disposed)return;const t=duration?Math.min(1,(now-start)/duration):1;
      if(t>=.5&&!committed){this.index=index;this.changes++;this.hooks.commit(this.bundles[index]);committed=true;}
      this.hooks.transition(from,to,t*t*(3-2*t));
      this.hooks.fade(Math.abs(2*t-1));
      if(t<1)this.frame=requestAnimationFrame(tick);else{this.frame=0;this.hooks.fade(1);this.schedule();}
      this.update();
    };
    this.frame=requestAnimationFrame(tick);this.update();
  }
  dispose(retain=new Set<string>()){
    this.disposed=true;this.ready=false;this.pause();this.abort.abort();
    for(const b of this.bundles){for(const t of b.textures.values())t.dispose();for(const u of b.urls.values())if(!retain.has(u))URL.revokeObjectURL(u);b.textures.clear();b.urls.clear();}
    this.bundles=[];this.update();
  }
}
