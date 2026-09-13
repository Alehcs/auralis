// Run from web/. Compare generated shaders, including the untouched Phase5 path.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from '../../web/node_modules/typescript/lib/typescript.js';
import {Group,Mesh,SphereGeometry,MeshBasicMaterial,Texture} from '../../web/node_modules/three/build/three.module.js';
const web=path.resolve('.'),ev=path.resolve('../evidence/phase75');
const data=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const transpile=s=>ts.transpileModule(s,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const three=pathToFileURL(path.join(web,'node_modules/three/build/three.module.js')).href;
async function load(base){
 const shader=data(transpile(fs.readFileSync(path.join(base,'src/phase6/surface-shader.ts'),'utf8')));
 let s=fs.readFileSync(path.join(base,'src/phase5/visual-materials.ts'),'utf8');
 s=s.replace("'../phase6/surface-shader'",JSON.stringify(shader)).replace("'../phase6/surface-motion.mjs'",JSON.stringify(pathToFileURL(path.join(web,'src/phase6/surface-motion.mjs')).href)).replace("'three'",JSON.stringify(three));
 return (await import(data(transpile(s)))).polishMaterials;
}
const a=await load(ev+'/baseline'),b=await load(web),checks={};
for(const name of ['IllustrativeSphere','Layer_magnetogram','Layer_bplus','Layer_bminus']){
 function generated(polish){const root=new Group(),mat=new MeshBasicMaterial({map:new Texture()}),mesh=new Mesh(new SphereGeometry(1,8,4),mat);mesh.name=name;root.add(mesh);polish(root,name!=='IllustrativeSphere');const s={uniforms:{},vertexShader:'#include <begin_vertex>\n#include <project_vertex>',fragmentShader:'#include <map_fragment>\n#include <colorspace_fragment>'};mat.onBeforeCompile(s,null);return [s.vertexShader,s.fragmentShader];}
 checks[name]=JSON.stringify(generated(a))===JSON.stringify(generated(b));if(!checks[name])throw Error('Changed protected shader: '+name);
}
fs.writeFileSync(ev+'/unchanged-shaders.json',JSON.stringify(checks,null,2));console.log(checks);
