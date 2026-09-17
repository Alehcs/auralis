"""Generate public display metadata from verified releases; no inference or data edits."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];BACK=ROOT/'auralis-back'
result={}
for version in ('3.1','3.2'):
 suffix=version.replace('.','_');mp=BACK/f'models/coronium_v{suffix}_manifest.json';m=json.loads(mp.read_text());metrics=json.loads((BACK/f'models/coronium_v{suffix}_metrics.json').read_text())
 for name,expected in m['artifacts_sha256'].items():
  assert hashlib.sha256((BACK/name).read_bytes()).hexdigest()==expected,name
 onnx=BACK/f'models/best_coronium_v{suffix}.onnx'
 result[version]={'model_name':m['model_name'],'seed':m['seed'] if 'seed' in m else int(re.search(r'seed=(\d+)',metrics['official_mc_dropout']['protocol'])[1]),'epoch':m['best_epoch'],'parameters':m['parameters'],'onnx_bytes':onnx.stat().st_size,'input_contract':m['input_contract'],'target_contract':m['target_contract'],'runtime':m.get('runtime'),'manifest_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'onnx_sha256':m['artifacts_sha256'][str(onnx.relative_to(BACK))],'metrics':{'deterministic':metrics['serving_deterministic']['onnx'],'mc':metrics.get('official_mc_dropout',{}).get('metrics')}}
(ROOT/'auralis-front/src/lib/release-presentation.json').write_text(json.dumps(result,indent=2)+'\n')
