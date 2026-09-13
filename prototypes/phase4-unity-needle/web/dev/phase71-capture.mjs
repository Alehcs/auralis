// Local-only evidence harness, imported only by Vite DEV + ?capture.
// Uses the rendered canvas and real controls; never mutates science or camera.
import {Context} from '@needle-tools/engine';
// WebGL discards its drawing buffer outside the frame. Read after a real render
// instead of accepting an empty but valid PNG as evidence of reproducibility.
function captureFrame(){return new Promise((resolve,reject)=>{
 const canvas=document.querySelector('#viewport needle-engine')?.shadowRoot?.querySelector('canvas');
 const context=Context.All.find(c=>c.renderer?.domElement===canvas);
 if(!context){reject(Error('Scene context unavailable'));return;}
 let finished=false;
 const remove=()=>{const i=context.post_render_callbacks.indexOf(capture);if(i>=0)context.post_render_callbacks.splice(i,1);};
 const timeout=setTimeout(()=>{finished=true;remove();reject(Error('No visible frame to capture'));},3000);
 const capture=()=>{if(finished)return;finished=true;clearTimeout(timeout);
   resolve(context.renderer.domElement.toDataURL('image/png'));queueMicrotask(remove);
 };context.post_render_callbacks.push(capture);
});}
const button=document.createElement('button');button.textContent='Grabar comparación 9 s';button.id='capture-evidence';
document.querySelector('.view-controls').append(button);
const output=document.createElement('textarea');output.id='capture-output';output.hidden=true;document.body.append(output);
button.onclick=async()=>{
 button.disabled=true;
 document.querySelector('#surface-reset').click();
 await new Promise(resolve=>setTimeout(resolve,600));
 const canvas=document.querySelector('#viewport needle-engine')?.shadowRoot?.querySelector('canvas');
 if(!canvas){button.disabled=false;throw Error('Scene canvas unavailable');}
 const stream=canvas.captureStream(30),chunks=[];
 const recorder=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp9',videoBitsPerSecond:18000000});
 const science=()=>JSON.parse(document.querySelector('#diagnostics').textContent);
 const before=science(),snapshots=[];
 const frozenFrames=[];
 const grabFrozen=async()=>frozenFrames.push({time:performance.now(),png:await captureFrame(),science:science()});
 const interval=setInterval(()=>snapshots.push(science()),500);
 recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
 recorder.onstop=async()=>{
   clearInterval(interval);stream.getTracks().forEach(t=>t.stop());
   const blob=new Blob(chunks,{type:recorder.mimeType});const reader=new FileReader();
   reader.onload=()=>{output.value=JSON.stringify({video:reader.result,before,after:science(),snapshots,frozenFrames,note:'9 s, fixed selected camera/date. 0–8 s running from t=0 at normal speed; 8–9 s paused. No physical AR.'});button.disabled=false;button.textContent='Grabar comparación 9 s';};reader.readAsDataURL(blob);
 };
 recorder.start();
 document.querySelector('#plasma').click();
 setTimeout(()=>document.querySelector('#plasma').click(),8000);
 setTimeout(grabFrozen,8400);setTimeout(grabFrozen,8900);
 setTimeout(()=>recorder.stop(),9000);
};
// Keep the viewport visible while invoking the existing measurement control.
const measure=document.createElement('button');measure.textContent='Comparar rendimiento 30 s';
measure.onclick=()=>document.querySelector('#sample').click();document.querySelector('.view-controls').append(measure);
const still=document.createElement('button');still.textContent='Capturar fotograma';
still.onclick=async()=>{
 still.disabled=true;
 try{output.value=JSON.stringify({png:await captureFrame(),science:JSON.parse(document.querySelector('#diagnostics').textContent)});}
 finally{still.disabled=false;}
};document.querySelector('.view-controls').append(still);
