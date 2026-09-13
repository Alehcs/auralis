import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import ts from 'typescript';
import {validateActivity} from '../src/phase6/activity.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
const seqBytes=await readFile(new URL('../public/phase6/sequence.json',import.meta.url));
const seq=JSON.parse(seqBytes),a=JSON.parse(await readFile(new URL('../public/phase6/activity.json',import.meta.url)));
const evidence=JSON.parse(await readFile(new URL('../public/phase6/sequence-evidence.json',import.meta.url)));
test('five spatial textures bind to exact source magnetograms and real Unity geometry',async()=>{
 assert.equal(validateActivity(a,seq,hash(seqBytes),evidence.unity_glb_sha256),a);
 assert.equal(new Set(a.entries.map(e=>e.solar.sha256)).size,5);
 for(const e of a.entries)assert.equal(hash(await readFile(new URL('../public'+e.solar.url,import.meta.url))),e.solar.sha256);
});
test('reject swapped solar maps, substituted source, wrong orientation or invalid disk',()=>{
 for(const mutate of [x=>x.entries.reverse(),x=>x.entries[1].solar=x.entries[0].solar,x=>x.entries[0].source_sha256='f'.repeat(64),x=>x.glb.sha256='f'.repeat(64),x=>x.entries[0].solar.origin='bottom_left',x=>x.entries[2].disk.radius=NaN]){
  const copy=structuredClone(a);mutate(copy);assert.throws(()=>validateActivity(copy,seq,hash(seqBytes),evidence.unity_glb_sha256));
 }
});

// Exercise the REAL controller with a deterministic animation clock, without
// requiring WebGL or simulating a physical XR device. DOM bindings stay empty.
let source=await readFile(new URL('../src/phase6/temporal.ts',import.meta.url),'utf8');
source=source.replace("import './timeline.css';",'');
for(const path of ['../phase5/contract.mjs','./sequence.mjs','./activity.mjs'])source=source.replaceAll("'"+path+"'",JSON.stringify(new URL(path,new URL('../src/phase6/temporal.ts',import.meta.url)).href));
source=source.replace("'three'",JSON.stringify(import.meta.resolve('three')));
const {TemporalSequence}=await import('data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText).toString('base64'));
test('controller returns identical textures in both directions; pause and rapid selection settle atomically',()=>{
 const original={document:global.document,matchMedia:global.matchMedia,requestAnimationFrame:global.requestAnimationFrame,cancelAnimationFrame:global.cancelAnimationFrame};
 let serial=0,queue=new Map(),committed,blend;
 global.document={querySelectorAll:()=>[]};global.matchMedia=()=>({matches:false});
 global.requestAnimationFrame=fn=>{queue.set(++serial,fn);return serial;};global.cancelAnimationFrame=id=>queue.delete(id);
 const controller=new TemporalSequence({commit:b=>committed=b,fade:()=>{},transition:(from,to,t)=>blend={from,to,t},status:()=>{}});
 controller.bundles=a.entries.map((e,i)=>({entry:seq.entries[i],activity:e,urls:new Map(),textures:new Map([['solar',{name:e.id,dispose(){}}]])}));
 const tick=offset=>{const work=[...queue.values()];queue.clear();for(const fn of work)fn(performance.now()+offset);};
 try{
  controller.activate();
  for(const index of [1,2,3,4,3,2,1,0,4,0]){
   const before=committed;controller.select(index);tick(5);assert.equal(committed,before);tick(300);
   assert.equal(committed,controller.bundles[index]);assert.equal(blend.to,committed);assert.equal(blend.t,1);
   assert.equal(committed.activity.source_sha256,committed.entry.source.sha256);
  }
  controller.select(4);tick(40);controller.pause();assert.equal(committed,controller.bundles[0]);assert.equal(blend.from,committed);assert.equal(blend.to,committed);
  controller.select(3);tick(160);controller.pause();assert.equal(committed,controller.bundles[3]);assert.equal(blend.to,committed);assert.equal(blend.t,1);
  controller.select(4);controller.select(1);tick(300);assert.equal(committed,controller.bundles[1]);assert.equal(queue.size,0);
  global.matchMedia=()=>({matches:true});controller.select(2);tick(0);assert.equal(committed,controller.bundles[2]);assert.equal(blend.t,1);
 }finally{controller.pause();Object.assign(global,original);}
});
