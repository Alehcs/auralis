import {readFile} from 'node:fs/promises';
import {test} from 'node:test';
import assert from 'node:assert/strict';
const root=new URL('../../../../',import.meta.url);
const ts=(await import(new URL('prototypes/phase4-unity-needle/web/node_modules/typescript/lib/typescript.js',root))).default;
const input=await readFile(new URL('auralis-front/src/lib/release-presentation.ts',root),'utf8');
const source=ts.transpileModule(input,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace("'./release-presentation.json'",JSON.stringify(new URL('auralis-front/src/lib/release-presentation.json',root).href)+" with { type: 'json' }");
const {releasePresentation,releaseLabel}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const data=JSON.parse(await readFile(new URL('auralis-front/src/lib/release-presentation.json',root)));
function stats(version){const r=data[version],m=r.metrics[version==='3.1'?'mc':'deterministic'];return {model_version:version,model_name:r.model_name,evaluation_protocol:version==='3.1'?'MC Dropout T=20':'deterministic ONNX mlas.disable_kleidiai=1',validation_observations:263,mae:m.mae,rmse:m.rmse,r2_score:m.r2,mape:m.mape,serving_deterministic:{onnx:r.metrics.deterministic}};}
test('both releases keep their own protocol, epoch, parameters and bytes',()=>{for(const v of ['3.1','3.2']){const s=stats(v),r=releasePresentation(s);assert.equal(r.epoch,v==='3.2'?27:40);assert.equal(r.parameters,206875);assert.equal(r.onnx_bytes,835234);assert.match(releaseLabel(s,'es'),/época/);}});
test('unavailable identity never yields substitute metrics',()=>{assert.equal(releasePresentation(null),null);assert.equal(releasePresentation({...stats('3.2'),model_name:'Coronium V3.1'}),null);assert.equal(releasePresentation({...stats('3.2'),model_version:'unknown'}),null);});
test('reject V3.1 metrics under V3.2 identity and unevaluated MC',()=>{assert.equal(releasePresentation({...stats('3.1'),model_name:'Coronium V3.2',model_version:'3.2'}),null);assert.equal(releasePresentation({...stats('3.2'),evaluation_protocol:'MC Dropout'}),null);});
test('reject mixed deterministic values and nonfinite display numbers',()=>{assert.equal(releasePresentation({...stats('3.2'),mae:NaN}),null);assert.equal(releasePresentation({...stats('3.2'),serving_deterministic:stats('3.1').serving_deterministic}),null);});
test('actual HTTP control responses and frozen Site retain matching identity',async()=>{
 for(const v of ['3.1','3.2']) {
  const saved=JSON.parse(await readFile(new URL(`http-${v}.json`,import.meta.url)));
  assert.ok(releasePresentation(saved['/api/stats'].body));
  for(const protocol of ['mc','deterministic']) {
   const record=saved[`/api/results-comparison?protocol=${protocol}`];
   if(record.status===503){assert.equal(data[v].metrics[protocol],null);continue;}
   const rows=record.body;assert.equal(rows.length,263);
   assert.ok(Math.abs(rows.reduce((s,r)=>s+Math.abs(r.predicted-r.real),0)/263-data[v].metrics[protocol].mae)<1e-6);
  }
 }
 const frozen=JSON.parse(await readFile(new URL('auralis-front/public/demo/responses.json',root)));
 assert.ok(releasePresentation(frozen['/api/stats']));
});
