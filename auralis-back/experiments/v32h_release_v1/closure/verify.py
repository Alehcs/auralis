"""Read-only final closure audit; no inference, export or benchmark."""
import hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BACK=ROOT/'auralis-back'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_map(mapping,root):
 for name,value in mapping.items():
  expected=value['sha256'] if isinstance(value,dict) else value
  assert digest(root/name)==expected, name
 return len(mapping)
protected=json.loads((HERE/'protected.json').read_text())
counts={'closure_protected':verify_map(protected,ROOT)}
preflight=json.loads((HERE.parent/'preflight.json').read_text())
counts['prior_research_sources']=verify_map(preflight['verified_sources'],ROOT)
f=BACK/'experiments/v32f_scientific_package_v1/package'
counts['f_artifacts']=verify_map(json.loads((f/'artifact_hashes.json').read_text()),f)
assert len(list((f/'figures').glob('*.png')))==26
manifest=json.loads((BACK/'models/coronium_v3_2_manifest.json').read_text())
counts['release_artifacts']=verify_map(manifest['artifacts_sha256'],BACK)
assert manifest['seed']==42 and manifest['best_epoch']==27 and manifest['parameters']==206875
assert manifest['runtime']['session_config']=={'mlas.disable_kleidiai':'1'}
sys.path.insert(0,str(BACK/'src'))
from models import active_model
assert active_model.DEFAULT_VERSION=='3.2'
active_model.load_version('3.2');active_model.load_version('3.1')
# Check local Markdown targets in edited active docs (anchors checked only for file existence).
docs=[ROOT/'README.md',ROOT/'RESEARCH_DOSSIER_MASTER.md',HERE/'REPORT.md',HERE.parent/'RUNBOOK.md',HERE.parent/'REPORT.md',HERE.parent/'PRUEBA-PC-TELEFONO.md',HERE.parent/'activation/REPORT.md']
broken=[];n=0
for p in docs:
 for link in re.findall(r'\]\(([^\s)]+)\)',p.read_text()):
  if ':' in link or link.startswith('#'):continue
  target=link.split('#')[0];n+=1
  if not (p.parent/target).exists():broken.append([str(p.relative_to(ROOT)),target])
assert not broken,broken
print(json.dumps({'verified':True,'counts':counts,'figure_triples':26,'local_document_links':n,'release':'3.2 C1_s42 epoch27','v31_recovery_artifacts_verified':True,'inference_executed':False},indent=2))
