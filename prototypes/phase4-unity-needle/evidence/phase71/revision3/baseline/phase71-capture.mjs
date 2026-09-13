// Local-only evidence harness, imported only by Vite DEV + ?capture.
// Uses the rendered canvas and real controls; never mutates science or camera.
const button=document.createElement('button');button.textContent='Grabar evidencia 10 s';button.id='capture-evidence';
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
 const interval=setInterval(()=>snapshots.push(science()),500);
 recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
 recorder.onstop=async()=>{
   clearInterval(interval);stream.getTracks().forEach(t=>t.stop());
   const blob=new Blob(chunks,{type:recorder.mimeType});const reader=new FileReader();
   reader.onload=()=>{output.value=JSON.stringify({video:reader.result,before,after:science(),snapshots,note:'Fixed camera, first HMI. 0–2 s frozen t=0; 2–8 s running; 8–10 s paused. No physical AR.'});button.disabled=false;button.textContent='Evidencia grabada';};reader.readAsDataURL(blob);
 };
 recorder.start();
 setTimeout(()=>document.querySelector('#plasma').click(),2000);
 setTimeout(()=>document.querySelector('#plasma').click(),8000);
 setTimeout(()=>recorder.stop(),10000);
};
