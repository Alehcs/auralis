import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateState, checkedLayer, clampScale, verifyExport } from '../src/phase5/contract.mjs';

const stateBytes=await readFile(new URL('../public/phase5/state.json',import.meta.url));
const state=JSON.parse(stateBytes);
const evidence=JSON.parse(await readFile(new URL('../public/phase5/export-evidence.json',import.meta.url)));
const glb=await readFile(new URL('../public/phase5/Phase5Solar.glb',import.meta.url));
const buffer=b=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);

test('accepts the frozen first-state contract and exported evidence',async()=>{
  assert.equal(validateState(state).state.id,'hmi-2022-03-24');
  await verifyExport(buffer(glb),evidence,buffer(stateBytes));
});
test('rejects another state, false time, MC protocol, invented WCS and negative channel',()=>{
  for(const mutate of [s=>s.state.order=2,s=>s.state.observation.time.record_utc='2022-03-25T00:00:53.000Z',s=>s.state.coronium_results.protocol='mc',s=>s.state.observation.region_context.wcs={},s=>s.state.derived.polarity.b_minus_magnitude_mean=-1,s=>s.layers.bplus.url='https://untrusted.example/image.png']){
    const changed=structuredClone(state);mutate(changed);assert.throws(()=>validateState(changed));
  }
});
test('rejects damaged GLB, other scene provenance and mismatched scientific values',async()=>{
  const damaged=Buffer.from(glb);damaged[200]^=1;
  await assert.rejects(verifyExport(buffer(damaged),evidence,buffer(stateBytes)));
  await assert.rejects(verifyExport(buffer(glb),{...evidence,scene:'Assets/Scenes/Phase4Probe.unity'},buffer(stateBytes)));
  const changed=structuredClone(state);changed.state.coronium_results.prediction_si=9;
  await assert.rejects(verifyExport(buffer(glb),evidence,buffer(Buffer.from(JSON.stringify(changed)))));
});
test('limits layers and scale to Phase5 controls',()=>{
  assert.equal(checkedLayer('bminus'),'bminus');assert.throws(()=>checkedLayer('flare'));
  assert.equal(clampScale(-1),.4);assert.equal(clampScale(4),1.5);assert.throws(()=>clampScale(NaN));
});
