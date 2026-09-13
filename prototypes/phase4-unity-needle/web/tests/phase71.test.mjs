import {test} from 'node:test';
import assert from 'node:assert/strict';
import {SurfaceClock,SURFACE_SEED} from '../src/phase6/surface-motion.mjs';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
import {Mesh,MeshBasicMaterial,Group,SphereGeometry,Texture} from 'three';

test('presentation clock freezes hidden time, clamps gaps, resumes and resets reproducibly',()=>{
 const a=new SurfaceClock(); a.tick(0,true); a.tick(16,true);a.tick(32,true);assert.equal(a.time,.032);
 a.running=false;a.tick(48,true);assert.equal(a.time,.032);
 a.running=true;a.tick(64,false);assert.equal(a.time,.032);
 a.sync(100000);a.tick(100016,true);assert.equal(a.time,.048);
 a.reset(100016);assert.equal(a.time,0);assert.equal(a.running,false);
 a.running=true;a.tick(100032,true);a.tick(100048,true);assert.equal(a.time,.032);
 a.tick(Infinity,true);assert.equal(a.time,.032);
 a.tick(200000,true);assert.equal(a.time,.132);assert.equal(SURFACE_SEED,71);
});

const moduleUrl=async(path,replacements={})=>{
 let source=await readFile(new URL(path,import.meta.url),'utf8');
 for(const [from,to]of Object.entries(replacements))source=source.replaceAll(from,to);
 return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
};
const shader=await moduleUrl('../src/phase6/surface-shader.ts');
const materialUrl=await moduleUrl('../src/phase5/visual-materials.ts',{
 "'three'":JSON.stringify(import.meta.resolve('three')),
 "'../phase6/surface-shader'":JSON.stringify(shader),
 "'../phase6/surface-motion.mjs'":JSON.stringify(new URL('../src/phase6/surface-motion.mjs',import.meta.url).href),
});
const {polishMaterials}=await import(materialUrl);
test('extends existing Unity mesh material; scientific planes have no moving UVs or surface transfer',()=>{
 const root=new Group(),geometry=new SphereGeometry(),solar=new Mesh(geometry,new MeshBasicMaterial({map:new Texture()}));solar.name='IllustrativeSphere';root.add(solar);
 const planes=['magnetogram','bplus','bminus'].map(name=>{const m=new Mesh(geometry,new MeshBasicMaterial({map:new Texture()}));m.name='Layer_'+name;root.add(m);return m;});
 const originals=[solar,...planes].map(m=>m.material);const visual=polishMaterials(root,true);
 const compile=m=>{const s={uniforms:{},vertexShader:'#include <begin_vertex>\n#include <project_vertex>',fragmentShader:'#include <map_fragment>\n#include <colorspace_fragment>'};m.material.onBeforeCompile(s);return s;};
 const s=compile(solar);assert.equal(s.uniforms.uIllustrationTime,visual.time);
 assert.equal(s.uniforms.uGuidePlus,visual.guidePlus);assert.match(s.fragmentShader,/texture2D\(map,vMapUv\)/);
 assert.doesNotMatch(s.fragmentShader,/mix\(texture2D\(uSolarFrom/);
 assert.match(s.vertexShader,/vSolarLocal=position/);assert.doesNotMatch(s.vertexShader,/position\s*\+=/);
 for(const plane of planes){const p=compile(plane);assert.match(p.fragmentShader,/#include <map_fragment>/);assert.doesNotMatch(p.fragmentShader,/solarNoise|guideUv|flowUv/);}
 assert.deepEqual([solar,...planes].map(m=>m.material),originals);
 visual.time.value=10;assert.equal(s.uniforms.uIllustrationTime.value,10);
 geometry.dispose();for(const m of [solar,...planes]){m.material.map.dispose();m.material.dispose();}
});

test('original Unity decoration survives temporal map replacement and is released exactly once',()=>{
 const original=new Texture(),stateAtlas=new Texture(),root=new Group();
 const sphere=new Mesh(new SphereGeometry(),new MeshBasicMaterial({map:original}));
 sphere.name='IllustrativeSphere';root.add(sphere);
 let disposed=0;original.addEventListener('dispose',()=>disposed++);
 const visual=polishMaterials(root,true);
 sphere.material.map=stateAtlas;
 const shader={uniforms:{},vertexShader:'#include <begin_vertex>\n#include <project_vertex>',fragmentShader:'#include <map_fragment>\n#include <colorspace_fragment>'};
 sphere.material.onBeforeCompile(shader);
 assert.equal(shader.uniforms.uDecoration.value,original);
 assert.equal(sphere.material.map,stateAtlas);
 visual.dispose();visual.dispose();assert.equal(disposed,1);assert.equal(visual.decoration.value,null);
 stateAtlas.dispose();sphere.geometry.dispose();sphere.material.dispose();
});
