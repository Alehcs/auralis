import {timeDomain,position,eventLayout,elapsed,dateLabel,utcLabel} from './history.mjs';

const node=(tag,text,className)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(className)e.className=className;return e;};
const magneticName=s=>s.replaceAll('Beta','β').replaceAll('Gamma','γ').replaceAll('Delta','δ').replaceAll('-','');

// One selection shared by web and Needle's AR DOM overlay. Events are inspection
// targets only: choosing one pauses the HMI controller and never calls commit.
export class ScientificContext {
  constructor(context,actions){
    this.context=context;this.actions=actions;this.stateId=context.states[0].id;
    this.eventId=null;this.enabled=false;this.views=[];this.abort=new AbortController();
    this.sources=new Map(context.sources.map(s=>[s.id,s]));
  }
  bind(container,ar=false){
    if(ar){const legend=node('p','Observación real HMI/SRS · resultado de Coronium SI · recreación visual 3D · evento externo GOES','science-legend');container.prepend(legend);}
    const oldAxis=container.querySelector('.time-axis');
    const scroller=node('div',null,'science-axis-scroll');scroller.tabIndex=0;
    scroller.setAttribute('aria-label',(ar?'AR: ':'')+'Timeline UTC; desliza horizontalmente');
    const track=node('div',null,'science-axis');scroller.append(track);
    const axis=node('div',null,'science-axis-inner');track.append(axis);
    const domain=timeDomain(this.context),layout=eventLayout(this.context);
    axis.style.height=(215+56*Math.max(...layout.map(e=>e.lane)))+'px';
    const lastPosition=position(this.context.states.at(-1).record_utc,domain);
    const post=node('div','Sin más magnetogramas','post-observation');post.style.left=lastPosition*100+'%';axis.append(post);
    axis.append(node('span','OBSERVACIONES HMI · 00:00:53 UTC','axis-row-label'));
    // Keep the five existing state buttons and their controller listeners.
    const states=node('div',null,'hmi-markers');axis.append(states);
    for(const [i,b] of [...oldAxis.querySelectorAll('button')].entries()){
      const s=this.context.states[i];b.style.setProperty('--position',position(s.record_utc,domain)*100+'%');
      b.textContent=dateLabel(s.record_utc)+' · '+magneticName(s.region_context.magnetic_type);states.append(b);
    }
    oldAxis.replaceWith(scroller);
    axis.append(node('span','EVENTOS GOES · MARCA EN EL PICO UTC','axis-row-label event-row-label'));
    const events=node('div',null,'event-markers');axis.append(events);
    for(const [i,e] of this.context.events.entries()){
      const b=node('button',null,'event-marker');b.type='button';b.dataset.eventId=e.id;
      b.setAttribute('aria-label',(ar?'AR: ':'')+'Evento '+e.goes_class+' · '+utcLabel(e.peak_utc));
      b.style.setProperty('--position',layout[i].position*100+'%');b.style.setProperty('--lane',String(layout[i].lane));
      b.append(node('strong','◆ '+e.goes_class),node('span',dateLabel(e.peak_utc)+' '+e.peak_utc.slice(11,16)));
      b.addEventListener('click',()=>this.selectEvent(e.id),{signal:this.abort.signal});events.append(b);
    }
    const note=container.querySelector('.time-note-real');note.textContent='UTC proporcional · desliza la escala. Cinco magnetogramas y seis eventos externos seleccionados; catálogo no exhaustivo. Play recorre solo los estados HMI; 2 s por estado y fundido gráfico.';
    const chooser=node('label','Evento histórico ','event-chooser');const select=node('select');select.setAttribute('aria-label',(ar?'AR: ':'')+'Elegir evento histórico');select.dataset.eventSelect='true';
    const empty=node('option','Selecciona un evento');empty.value='';select.append(empty);
    for(const e of this.context.events){const opt=node('option',e.goes_class+' · '+utcLabel(e.peak_utc));opt.value=e.id;select.append(opt);}
    select.addEventListener('change',()=>select.value?this.selectEvent(select.value):this.showState(),{signal:this.abort.signal});chooser.append(select);container.append(chooser);
    const inspector=node('section',null,'science-inspector');inspector.setAttribute('aria-label',(ar?'AR: ':'')+'Contexto científico seleccionado');inspector.setAttribute('aria-live','polite');container.append(inspector);
    container.addEventListener('click',event=>{if(event.target.closest('[data-state-index],[data-time="prev"],[data-time="next"],[data-time="play"]'))this.showState();},{capture:true,signal:this.abort.signal});
    this.views.push({container,inspector,select,scroller,ar});this.render();
  }
  setEnabled(value){this.enabled=value;this.render();}
  setState(id){if(id===this.stateId)return;this.stateId=id;this.eventId=null;this.render();this.center('state');}
  showState(){this.eventId=null;this.render();}
  selectEvent(id){
    if(!this.enabled||!this.context.events.some(e=>e.id===id))return;
    this.actions.pause();this.eventId=id;this.render();this.center('event');
  }
  center(kind){
    const index=this.context.states.findIndex(s=>s.id===this.stateId);
    for(const view of this.views){const target=view.container.querySelector(kind==='event'?`[data-event-id="${this.eventId}"]`:`[data-state-index="${index}"]`);if(!target||!view.scroller.clientWidth)continue;const a=target.getBoundingClientRect(),b=view.scroller.getBoundingClientRect();view.scroller.scrollLeft+=a.left-b.left-(view.scroller.clientWidth-a.width)/2;}
  }
  provenance(ref,line,raw){
    const source=this.sources.get(ref),details=node('details',null,'context-source');details.append(node('summary','Fuente conservada · '+source.path.split('/').at(-1)+(line?' · línea '+line:'')));
    if(raw)details.append(node('pre',raw));
    const link=node('a','Abrir snapshot de Fase 2');link.href=source.snapshot_url;link.target='_blank';link.rel='noopener';details.append(link);
    details.append(node('p','Consulta original: '+source.retrieved_utc));details.append(node('code','SHA-256 '+source.sha256));
    return details;
  }
  render(){
    const s=this.context.states.find(s=>s.id===this.stateId),r=s.region_context;
    const event=this.context.events.find(e=>e.id===this.eventId);
    for(const view of this.views){
      view.select.disabled=!this.enabled;view.select.value=this.eventId??'';
      for(const b of view.container.querySelectorAll('[data-event-id]')){b.disabled=!this.enabled;b.setAttribute('aria-pressed',String(b.dataset.eventId===this.eventId));}
      const panel=view.inspector;panel.replaceChildren();
      if(event){
        panel.append(node('p','EVENTO HISTÓRICO EXTERNO · GOES '+event.satellite,'context-kind event-kind'));
        panel.append(node('h3',event.goes_class+' · NOAA '+event.noaa+' · pico '+utcLabel(event.peak_utc)));
        panel.append(node('p','Inicio '+utcLabel(event.start_utc)+' · fin '+utcLabel(event.end_utc)));
        const rel=event.temporal_relation,previous=this.context.states.find(x=>x.id===rel.preceding_state_id),next=this.context.states.find(x=>x.id===rel.following_state_id);
        panel.append(node('p',elapsed(rel.seconds_after_preceding_state)+' después del HMI del '+dateLabel(previous.record_utc)+'. '+(next?'Entre los estados '+dateLabel(previous.record_utc)+' y '+dateLabel(next.record_utc)+'.':'Posterior al último estado; no hay otro magnetograma seleccionado.'),'event-relation'));
        panel.append(node('p','Ningún estado seleccionado captura este evento. El Sol conserva el HMI del '+utcLabel(s.record_utc)+'. Coronium estima SI actual; no anticipa llamaradas.','context-limit'));
        const button=node('button','Ver HMI anterior · '+dateLabel(previous.record_utc));button.disabled=!this.enabled;
        button.onclick=()=>{this.showState();this.actions.selectState(this.context.states.indexOf(previous));this.center('state');};panel.append(button);
        panel.append(this.provenance(event.source_ref,event.source_line,event.raw_line));
      }else{
        panel.append(node('p','OBSERVACIÓN REAL · CONTEXTO REGIONAL SRS','context-kind'));
        panel.append(node('h3','NOAA '+r.noaa+' / HARP '+r.harp+' · '+r.magnetic_type+' · '+dateLabel(s.record_utc)));
        const i=this.context.states.indexOf(s),prev=this.context.states[i-1];
        const change=prev?(prev.region_context.magnetic_type===r.magnetic_type?'Misma clasificación que el estado anterior.':'Cambio catalogado: '+prev.region_context.magnetic_type+' → '+r.magnetic_type+'.'):'Primer estado seleccionado.';
        panel.append(node('p',change+' Ubicación SRS: '+r.location.reported+'.'));
        const details=node('details',null,'context-source');details.append(node('summary','Validez SRS, alcance regional y fuentes'));
        details.append(node('p','Área catalogada: '+r.area_millionths_solar_hemisphere+' millonésimas del hemisferio solar.'));
        details.append(node('p','SRS válido '+utcLabel(r.location.valid_utc)+' · emitido '+utcLabel(r.location.issued_utc)+'. HMI '+s.record_utc.slice(11,19)+' UTC.','context-times'));
        details.append(node('p','HARP 8088 comparte asociación de catálogo con NOAA 12976, 12977 y 12984; no es una máscara exclusiva. SRS no está registrado en píxeles. SI y mapas abarcan el disco completo.','context-limit'));
        const boundaryEvents=this.context.events.filter(e=>e.temporal_relation.preceding_state_id===s.id);
        panel.append(node('p',boundaryEvents.length?'Eventos posteriores a este HMI: '+boundaryEvents.map(e=>e.goes_class+' ('+utcLabel(e.peak_utc)+')').join(' · ')+'.':'No hay eventos seleccionados en el intervalo hasta el siguiente HMI; no significa ausencia de actividad.','context-events'));
        if(s===this.context.states.at(-1))panel.append(node('p','X1.3: 17 h 36 min 07 s después de este HMI; fuera del magnetograma.','event-relation'));
        details.append(this.provenance(r.location.source_ref,r.location.source_line,r.location.raw_line));
        details.append(this.provenance(r.harp_source_ref,null,null));panel.append(details);
      }
    }
    this.actions.status({contextStateId:this.stateId,selectedEventId:this.eventId,selectedEventPeak:event?.peak_utc??null,contextMagneticType:r.magnetic_type,contextManifestVerified:true});
  }
  dispose(){this.abort.abort();this.views=[];}
}
