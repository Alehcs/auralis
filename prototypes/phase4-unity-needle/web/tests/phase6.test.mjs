import {test} from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {validateSequence,nextIndex,timelinePositions} from '../src/phase6/sequence.mjs';import {digest} from '../src/phase5/contract.mjs';
const bytes=await readFile(new URL('../public/phase6/sequence.json',import.meta.url));const m=JSON.parse(bytes);
test('five frozen observations retain chronological gaps, values and final SI decline',()=>{
 assert.equal(validateSequence(m),m);assert.deepEqual(timelinePositions(m.entries),[0,1/6,4/6,5/6,1]);
 assert.ok(m.entries[4].state.observation.target_si.value<m.entries[3].state.observation.target_si.value);
 assert.ok(m.entries[4].state.coronium_results.prediction_si>m.entries[3].state.coronium_results.prediction_si);
});
test('forwards/backwards cover all states and stop at boundaries',()=>{
 let i=0;const a=[i];for(let n=0;n<6;n++){i=nextIndex(i,1);a.push(i);}assert.deepEqual(a,[0,1,2,3,4,4,4]);
 const b=[i];for(let n=0;n<6;n++){i=nextIndex(i,-1);b.push(i);}assert.deepEqual(b,[4,3,2,1,0,0,0]);
});
test('rejects swapped states, fake dates, wrong channel files and MC results',()=>{
 for(const mutate of [x=>x.entries.reverse(),x=>x.entries[2].state.observation.time.record_utc='2022-03-26T00:00:53.000Z',x=>x.entries[1].layers.bminus.url=x.entries[1].layers.bplus.url,x=>x.entries[4].state.coronium_results.protocol='mc',x=>x.entries.pop()]){const c=structuredClone(m);mutate(c);assert.throws(()=>validateSequence(c));}
});
test('all 15 map files and the sequence match their frozen display hashes',async()=>{
 const evidence=JSON.parse(await readFile(new URL('../public/phase6/sequence-evidence.json',import.meta.url)));assert.equal(await digest(bytes),evidence.sequence_sha256);
 for(const e of m.entries)for(const a of Object.values(e.layers)){const b=await readFile(new URL('../public'+a.url,import.meta.url));assert.equal(await digest(b),a.sha256);}
});
