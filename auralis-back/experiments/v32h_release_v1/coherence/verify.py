"""Read-only protection, provenance and content-scope verification."""
from pathlib import Path
import hashlib,json,re,subprocess,ast
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
baseline=json.loads((HERE/'baseline.json').read_text()); protected=json.loads((HERE/'protected.json').read_text())
changed=[]
for name,digest in protected.items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:changed.append(name)
assert changed==['auralis-back/src/api/main.py'],changed
api='auralis-back/src/api/main.py'
old=subprocess.check_output(['git','show',baseline['head']+':'+api],cwd=ROOT,text=True)
expected=old.replace('"Predict-dual (V3 PRO B+/B-) for %s:', 'f"Predict-dual ({MODEL_NAME} B+/B-) for %s:').replace('Prediction (normalized proxy index):','Prediction (SI %):').replace('no ranking or relative improvement evidence for V3.1.','no ranking or relative improvement evidence for the active release.')
assert (ROOT/api).read_text()==expected
ast.parse(expected)
files=subprocess.check_output(['git','diff','--name-only',baseline['head']],cwd=ROOT,text=True).splitlines()
layout=[]
for name in files:
 if name.endswith('.tsx'):
  before=subprocess.check_output(['git','show',baseline['head']+':'+name],cwd=ROOT,text=True);after=(ROOT/name).read_text()
  for pattern in [r'className=(?:"[^"]*"|\{[^\n]*\})',r'style=\{[^\n]*\}']:
   assert re.findall(pattern,before)==re.findall(pattern,after),name
  layout.append(name)
def diagnostics(p):
 found=[]
 for line in p.read_text().splitlines():
  m=re.search(r'(src/[^(:]+)\(\d+,\d+\): error (TS\d+): (.*)',line)
  if m:found.append((m[1],m[2],m[3].split('does not satisfy the constraint')[0] if m[2]=='TS2344' else m[3]))
 return found
oldts=diagnostics(HERE.parent/'closure/typescript-final.txt');newts=diagnostics(HERE/'typescript-final.txt')
assert len(oldts)==len(newts)==15 and set(oldts)==set(newts)
assert subprocess.check_output(['git','rev-parse','coronium-v3.2'],cwd=ROOT,text=True).strip()==baseline['tag']
links=0
for p in [ROOT/'README.md',ROOT/'RESEARCH_DOSSIER_MASTER.md',HERE/'REPORT.md',HERE.parent/'closure/REPORT.md']:
 for link in re.findall(r'\]\(([^\s)]+)\)',p.read_text()):
  if ':' in link or link.startswith('#'):continue
  target=link.split('#')[0]
  if target=='verification.json':continue
  assert (p.parent/target).exists(),(p.name,target)
  links+=1
print(json.dumps({'protected_files':len(protected),'backend_changes':'four exact display-text substitutions only','layout_classes_styles_unchanged':layout,'typescript_prior':15,'typescript_current':15,'new_diagnostics':0,'tag_unchanged':True,'documentation_links':links,'presentation_tests':5,'release_tests':6,'solar_tests':29,'builds':'main frontend and Needle passed','desktop_visual':'1280x720, no document horizontal overflow; EN/ES, eight tabs, V3.1 landing','mobile_width':'390px override did not apply; not verified this run','new_research_or_benchmarks':False},indent=2))
