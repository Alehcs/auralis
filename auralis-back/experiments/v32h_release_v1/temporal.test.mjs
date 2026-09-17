import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {applyReleasePredictions,selectReleasePredictions} from '../../../prototypes/phase4-unity-needle/web/src/phase6/release-predictions.mjs';
const viewer=new URL('../../../prototypes/phase4-unity-needle/web/public/phase6/',import.meta.url);
const original=JSON.parse(readFileSync(new URL('sequence.json',viewer)));
const release=JSON.parse(readFileSync(new URL('releases/coronium-v3.2-r1.json',viewer)));
test('five states: only numeric results and model provenance change',()=>{
 const copy=structuredClone(original), revised=applyReleasePredictions(original,release);
 assert.deepEqual(original,copy);
 assert.equal(revised.model.version,'3.2');
 for(let i=0;i<5;i++){
  const {coronium_results:oldResult,...oldState}=original.entries[i].state;
  const {coronium_results:newResult,...newState}=revised.entries[i].state;
  assert.deepEqual(newState,oldState);assert.deepEqual(revised.entries[i].layers,original.entries[i].layers);
  assert.equal(newResult.prediction_si,release.entries[i].prediction_si);
  assert.notEqual(oldResult.prediction_si,newResult.prediction_si);
 }
});
test('no explicit release preserves V3.1 and performs no overlay fetch',async()=>{
 assert.equal(await selectReleasePredictions(original,()=>{throw Error('unexpected fetch');},''),original);
});
test('mismatch, unknown release and corrupted bytes fail without fallback',async()=>{
 const bad=structuredClone(release);bad.entries[0].state_id='wrong';
 assert.throws(()=>applyReleasePredictions(original,bad));
 await assert.rejects(()=>selectReleasePredictions(original,()=>{},'?release=bad'));
 await assert.rejects(()=>selectReleasePredictions(original,async()=>new TextEncoder().encode('{}'),'?release=3.2'));
});
