"""Refresh static Sites with verified V3.2 saved results; zero model inferences.

Reuses the existing demo's sixteen cases/images, E.1 predictions and H temporal
revision. Legacy V3.1 Grad-CAM files stay preserved but are not advertised as V3.2.
"""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
from datetime import datetime,timezone
import copy,csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1];BACK=ROOT/'auralis-back';OUT=ROOT/'auralis-front/public/demo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((OUT/'responses.json').read_text());manifest_path=BACK/'models/coronium_v3_2_manifest.json';manifest=json.loads(manifest_path.read_text())
assert manifest['promotion']['authorized'] and manifest['seed']==42 and manifest['best_epoch']==27
for path,digest in manifest['artifacts_sha256'].items():assert sha(BACK/path)==digest,path
requests=[]
def read(route):
 assert route.startswith('/api/') and not any(x in route for x in ['predict','explain','faithfulness','upload'])
 requests.append(route)
 with urlopen('http://localhost:8000'+route,timeout=120) as res:return json.load(res)
responses={'/api/stats':read('/api/stats')};assert responses['/api/stats']['model_version']=='3.2'
assert responses['/api/stats']['available_protocols']==['deterministic']
for route in ['/api/images/list','/api/benchmark','/api/experiments','/api/results-comparison?protocol=deterministic','/api/polarity-series?limit=48','/api/agents/full-report']:
 responses[route]=read(route)
for e in responses['/api/experiments']:
 route='/api/experiments/'+quote(e['metadata_file']);responses[route]=read(route)
responses['/api/results-comparison']=responses['/api/results-comparison?protocol=deterministic']
assert len(responses['/api/results-comparison'])==263
validation=BACK/'models/coronium_v3_2_validation.csv';temporal=BACK/'models/coronium_v3_2_temporal.json'
with validation.open() as f:values={x['processed_file']:float(x['kleidiai_off_si']) for x in csv.DictReader(f)}
revision=json.loads(temporal.read_text());assert revision['model']['seed']==42
for x in revision['entries']:
 if x['filename'] in values:assert values[x['filename']]==x['prediction_si']
 values[x['filename']]=x['prediction_si']
selectable=old['/demo/selectable-images'];assert selectable['total']==16
responses['/demo/selectable-images']=selectable
# Do not silently use V3.1 explanations for V3.2 numerical results.
responses['/demo/gradcam-images']=[]
source_response=BACK/'experiments/v32h_release_v1/activation/normal_default/predictions.json'
template=json.loads(source_response.read_text())['predict'];assert template['model_version']=='3.2'
records=[]
for image in selectable['images']:
 name=image['filename'];raw=values[name];value=round(raw,4);p=copy.deepcopy(template)
 level,label,symbol,color=('Low','Low / Normal Activity','C','#22c55e') if value<1.41 else (('Medium','Medium / Moderate Activity','M','#f97316') if value<1.75 else ('High','High / High Activity','X','#ef4444'))
 p.update(sunspot_index=value,risk_level=level,confidence=None,uncertainty=None,confidence_method='not computed for saved Site results',uncertainty_method='not computed for saved Site results; no calibrated uncertainty',classification={'level':level,'label':label,'flare_class':symbol,'hex_color':color,'interpretation':'Historical internal activity bands; not GOES flare classes'})
 for route in ['predict','predict-dual']:responses[f'/api/{route}/{quote(name)}']=p
 for kind in ['images','aia']:assert (OUT/kind/(name+'.png')).is_file()
 records.append({'filename':name,'si_full_precision':raw,'public_si':value,'model':'Coronium V3.2','seed':42})
responses['/health']={'status':'archived','model_name':'Coronium V3.2','model_version':'3.2','model_loaded':False,'device':'not_running'}
responses['/api/logs']=[{'filename':'demo-v32-archivada.txt','lines':['Demo estática: resultados guardados de Coronium V3.2 s42, época27. No hay inferencia ejecutándose en Sites.','16 casos conservados y263 resultados de validation de selección; no es test independiente.','SI procede de E.1 mitigada y la revisión temporal H, sin nuevas inferencias.','Confianza/ruido no calculados para estos resultados. Grad-CAM V3.2 no guardado para estos16 casos; las imágenes V3.1 no se reutilizan como V3.2.','Persisten deterioro tolerado en baja actividad y dudas XAI de borde/fondo.']}]
(OUT/'responses.json').write_text(json.dumps(responses,ensure_ascii=False,separators=(',',':')))
(OUT/'predictions-v32.json').write_text(json.dumps({'model_version':'3.2','seed':42,'epoch':27,'runtime':'kleidiai_off','entries':records},indent=2)+'\n')
sources=[manifest_path,validation,temporal,source_response,BACK/'models/coronium_v3_2_metrics.json']
result={'exported_at':datetime.now(timezone.utc).isoformat(),'model':'Coronium V3.2','seed':42,'epoch':27,'runtime':'kleidiai_off','new_inferences':0,'catalog_images':responses['/api/images/list']['total'],'selectable_saved_predictions':16,'saved_gradcam_cases':0,'historical_gradcam':'gradcam/ and gradcam-provenance.json preserve V3.1; inactive for V3.2','source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'read_only_requests':requests,'files':{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'responses':len(responses),'saved_predictions':len(records),'new_inferences':0,'gradcam_v31_not_mislabeled':True}))
