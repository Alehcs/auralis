// Package only the generated Sites-mode frontend; the solar iframe uses its own Site.
import { cp, mkdir, readFile, readdir, writeFile, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const source = path.join(root, 'auralis-front/dist');
const target = path.join(root, 'deployments/dashboard-sites/dist');
const scripts = await readdir(path.join(source, 'assets'));
const js = (await Promise.all(scripts.filter(x=>x.endsWith('.js')).map(x=>readFile(path.join(source,'assets',x),'utf8')))).join('\n');
if (!js.includes('Demo con resultados guardados') || !js.includes('auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site')) throw Error('Build with --mode sites before packaging.');
await rm(target, {recursive:true,force:true}); // Generated deployment output only.
await cp(source, target, {recursive:true});
await mkdir(path.join(target,'dashboard'), {recursive:true});
await cp(path.join(source,'index.html'), path.join(target,'dashboard/index.html'));
const files = {};
async function inventory(dir) {
  for (const entry of await readdir(dir,{withFileTypes:true})) {
    const file=path.join(dir,entry.name);
    if (entry.isDirectory()) await inventory(file);
    else files[path.relative(target,file)] = createHash('sha256').update(await readFile(file)).digest('hex');
  }
}
await inventory(target);
await writeFile(path.join(root,'deployments/dashboard-sites/build-evidence.json'),JSON.stringify({source:'../../auralis-front',mode:'sites',files},null,2)+'\n');
console.log(`Prepared ${Object.keys(files).length} generated dashboard files; no duplicated solar assets.`);
