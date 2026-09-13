import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {eventRelation,validateContext,timeDomain,position,eventLayout,elapsed} from '../src/phase7/history.mjs';
import {ScientificContext} from '../src/phase7/scientific-context.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
const bytes=await readFile(new URL('../public/phase6/sequence.json',import.meta.url));const seq=JSON.parse(bytes);
const contextBytes=await readFile(new URL('../public/phase7/context.json',import.meta.url));const c=JSON.parse(contextBytes);
test('SRS, six independent events and preserved source snapshots match frozen provenance',async()=>{
 assert.equal(validateContext(c,seq,hash(bytes)),c);
 assert.deepEqual(c.states.map(s=>s.region_context.magnetic_type),['Beta','Beta','Beta','Beta-Gamma','Beta-Gamma-Delta']);
 const evidence=JSON.parse(await readFile(new URL('../public/phase7/context-evidence.json',import.meta.url)));assert.equal(evidence.context_sha256,hash(contextBytes));
 for(const s of c.sources){const b=await readFile(new URL('../public'+s.snapshot_url,import.meta.url));assert.equal(hash(b),s.sha256);}
});
test('X1.3 remains 63367 seconds after state5; M4 and M2.2 stay between their correct observations',()=>{
 const x=c.events.find(e=>e.goes_class==='X1.3'),domain=timeDomain(c);
 assert.equal(elapsed(x.temporal_relation.seconds_after_preceding_state),'17 h 36 min 07 s');
 assert.deepEqual(eventRelation(x,c.states),{basis:'peak_utc',placement:'after_last_state',preceding_state_id:'hmi-2022-03-30',following_state_id:null,seconds_after_preceding_state:63367,captured_by_state_id:null});
 assert.ok(position(x.peak_utc,domain)>position(c.states[4].record_utc,domain));
 assert.deepEqual([eventRelation(c.events[0],c.states).preceding_state_id,eventRelation(c.events[2],c.states).preceding_state_id],['hmi-2022-03-28','hmi-2022-03-29']);
 const p=c.states.map(s=>position(s.record_utc,domain));assert.ok(Math.abs((p[2]-p[1])/(p[1]-p[0])-3)<1e-12);
 const layout=eventLayout(c);for(let i=0;i<layout.length;i++){assert.equal(layout[i].position,position(c.events[i].peak_utc,domain));for(let j=0;j<i;j++)if(layout[i].lane===layout[j].lane)assert.ok((layout[i].position-layout[j].position)*900>=124);}
});
test('reject false X capture, snapped event time, regional type rewrite and replacement source',()=>{
 for(const change of [x=>x.events[4].temporal_relation.captured_by_state_id='hmi-2022-03-30',x=>x.events[4].peak_utc=x.states[4].record_utc,x=>x.states[2].region_context.magnetic_type='Beta-Gamma-Delta',x=>x.events[2].source_ref='missing',x=>x.events[0].end_utc='2022-03-28T00:00:00Z',x=>x.events.pop(),x=>x.events.reverse()]){const copy=structuredClone(c);change(copy);assert.throws(()=>validateContext(copy,seq,hash(bytes)));}
});
test('selecting events pauses without selecting or replacing any HMI state; selection clears on real state change',()=>{
 let pauses=0,stateSelections=0,status;
 const history=new ScientificContext(c,{pause:()=>pauses++,selectState:()=>stateSelections++,status:s=>status=s});
 history.setEnabled(true);const original=history.stateId;
 for(const e of c.events){history.selectEvent(e.id);assert.equal(history.stateId,original);assert.equal(status.contextStateId,original);assert.equal(status.selectedEventId,e.id);}
 assert.equal(pauses,6);assert.equal(stateSelections,0);
 history.setState('hmi-2022-03-30');assert.equal(status.selectedEventId,null);assert.equal(status.contextMagneticType,'Beta-Gamma-Delta');
 history.selectEvent(c.events[4].id);history.showState();assert.equal(status.selectedEventId,null);
 history.setEnabled(false);history.selectEvent(c.events[0].id);assert.equal(status.selectedEventId,null);history.dispose();
});
