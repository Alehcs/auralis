import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import ts from '../../../../prototypes/phase4-unity-needle/web/node_modules/typescript/lib/typescript.js';

const root = fileURLToPath(new URL('../../../../', import.meta.url));
const read = path => readFileSync(new URL(path, `file://${root}`), 'utf8');
const baseline = JSON.parse(readFileSync(new URL('baseline.json', import.meta.url)));
const original = path => execFileSync('git', ['show', `${baseline.head}:${path}`], { cwd: root, encoding: 'utf8' });
const protectedFiles = JSON.parse(readFileSync(new URL('protected.json', import.meta.url)));
for (const [path, hash] of Object.entries(protectedFiles)) {
  assert.equal(createHash('sha256').update(readFileSync(root + path)).digest('hex'), hash, path);
}
const configPath = 'auralis-front/tsconfig.json';
const oldConfig = JSON.parse(original(configPath));
delete oldConfig.compilerOptions.ignoreDeprecations;
assert.deepEqual(JSON.parse(read(configPath)), oldConfig);
const packagePath = 'auralis-front/package.json';
const currentPackage = JSON.parse(read(packagePath));
assert.ok(currentPackage.scripts.typecheck.includes('tsconfig.node.json'));
delete currentPackage.scripts.typecheck;
assert.deepEqual(currentPackage, JSON.parse(original(packagePath)));
const translationsPath = 'auralis-front/src/lib/i18n/translations.ts';
const emit = source => ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
assert.equal(emit(read(translationsPath)), emit(original(translationsPath)), 'Translation runtime and all texts unchanged');

// Compare original JSX text and styling expressions, independently of type syntax.
function presentation(source) {
  const tree = ts.createSourceFile('component.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const values = [];
  function visit(node) {
    if ((ts.isJsxText(node) && node.getText(tree).trim()) || (ts.isJsxAttribute(node) && ['className', 'style'].includes(node.name.getText(tree)))) {
      values.push(node.getText(tree));
    }
    ts.forEachChild(node, visit);
  }
  visit(tree);
  return values;
}
const components = [
  'src/app/components/ui/chart.tsx',
  'src/features/dashboard/components/xai-faithfulness.tsx',
  'src/features/dashboard/magnetogram-panel.tsx',
  'src/features/dashboard/prediction-chart.tsx',
];
for (const path of components.map(path => 'auralis-front/' + path)) {
  assert.deepEqual(presentation(read(path)), presentation(original(path)), path);
}
assert.equal(execFileSync('git', ['rev-parse', 'coronium-v3.2'], { cwd: root, encoding: 'utf8' }).trim(), baseline.tag);
assert.equal(ts.version, '5.9.3');
const typecheck = execFileSync('npm', ['--prefix', 'auralis-front', 'run', 'typecheck'], { cwd: root, encoding: 'utf8' });
writeFileSync(new URL('typecheck.txt', import.meta.url), typecheck.trimEnd() + '\n');
const result = {
  protected_files_unchanged: Object.keys(protectedFiles).length,
  compiler: ts.version,
  only_config_change: 'removed unsupported ignoreDeprecations=6.0',
  full_src_and_vite_config_checked: true,
  translations_runtime_identical: true,
  jsx_text_and_styles_unchanged: components,
  model_tag_unchanged: true,
};
writeFileSync(new URL('verification.json', import.meta.url), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
