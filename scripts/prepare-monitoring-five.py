"""Archive five existing HMI cases and Grad-CAM figures for the static dashboard.

Run after export-sites-demo.py. Existing verified figures are reused; no serving
prediction, upload, model update or temporal-contract write is performed.
"""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'auralis-front/public/demo'
SEQUENCE = ROOT / 'prototypes/phase4-unity-needle/web/public/phase6/sequence.json'
RECORD = OUT / 'gradcam-provenance.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

sequence = json.loads(SEQUENCE.read_text())
responses = json.loads((OUT / 'responses.json').read_text())
template = json.loads((ROOT / 'auralis-back/reports/phase16_coronium_v3_1/live-http.json').read_text())['prediction']
source_paths = [SEQUENCE, ROOT / 'auralis-back/models/best_coronium_v3_1.pth',
                ROOT / 'auralis-back/src/api/main.py', ROOT / 'auralis-back/src/models/train_model.py',
                ROOT / 'auralis-back/src/processing/model_input.py']
for entry in sequence['entries']:
    path = ROOT / 'auralis-back' / entry['source']['path']
    assert sha(path) == entry['source']['sha256'], path
    source_paths.append(path)
source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
previous = json.loads(RECORD.read_text()) if RECORD.exists() else {}
assert not previous or previous['source_sha256'] == source_hashes, 'Sources changed; review before regenerating Grad-CAM.'
requests = []
files = {}
for entry in sequence['entries']:
    state = entry['state']
    filename = state['observation']['magnetogram']['filename']
    value = state['coronium_results']['api_display_4dp']
    level, label, symbol, color = ('Low', 'Low / Normal Activity', 'C', '#22c55e') if value < 1.41 else (
        ('Medium', 'Medium / Moderate Activity', 'M', '#f97316') if value < 1.75 else
        ('High', 'High / High Activity', 'X', '#ef4444'))
    prediction = {k: template[k] for k in ['model_name', 'model_version', 'input_contract', 'target_contract', 'output_units', 'model_status', 'prediction_method']}
    prediction.update(sunspot_index=value, risk_level=level, confidence=None, uncertainty=None,
                      classification={'level': level, 'label': label, 'flare_class': symbol, 'hex_color': color,
                                      'interpretation': 'Historical internal activity bands; not GOES flare classes'})
    for route in ['predict', 'predict-dual']:
        responses[f'/api/{route}/{quote(filename)}'] = prediction
    for kind, route in [('images', 'images'), ('aia', 'aia'), ('gradcam', 'explain-panels')]:
        path = OUT / kind / (filename + '.png')
        rel = str(path.relative_to(OUT))
        if rel in previous.get('files', {}):
            assert path.exists() and sha(path) == previous['files'][rel], path
        else:
            endpoint = f'/api/{route}/{quote(filename)}'
            with urlopen('http://localhost:8000' + endpoint, timeout=180) as response:
                data = response.read()
            assert data.startswith(b'\x89PNG\r\n\x1a\n'), endpoint
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
            requests.append(endpoint)
        files[rel] = sha(path)

names = [e['state']['observation']['magnetogram']['filename'] for e in sequence['entries']]
catalog = responses['/api/images/list']['images']
existing = {x['filename'] for x in responses['/demo/selectable-images']['images']}
selectable = [x for x in catalog if x['filename'] in existing | set(names)]
assert all(any(x['filename'] == name for x in selectable) for name in names)
responses['/demo/selectable-images'] = {'images': selectable, 'total': len(selectable)}
responses['/demo/gradcam-images'] = names
responses['/api/logs'][0]['lines'] = [
    'Resultados archivados; no hay inferencia activa.',
    '11 ejemplos HTTP y cinco estados HMI de marzo de 2022.',
    'Grad-CAM precalculado disponible para los cinco estados HMI.',
    'El análisis de nuevos archivos no está disponible.',
]
record = {'generated_at': previous.get('generated_at') or datetime.now(timezone.utc).isoformat(),
          'model': 'Coronium V3.1', 'layer': 'stage4.conv', 'method': 'Existing /api/explain-panels; PyTorch eval-mode forward/backward',
          'serving': 'Static PNG; no computation in Sites', 'source_sha256': source_hashes,
          'files': files, 'requests': previous.get('requests', []) + requests,
          'prediction_source': 'Frozen sequence api_display_4dp; no new ONNX prediction',
          'interpretation': 'Model attribution; not region segmentation, magnetic field or flare probability'}
RECORD.write_text(json.dumps(record, indent=2) + '\n')
(OUT / 'responses.json').write_text(json.dumps(responses, ensure_ascii=False, separators=(',', ':')))
manifest = json.loads((OUT / 'manifest.json').read_text())
manifest.update(selectable_saved_predictions=len(selectable), saved_gradcam_cases=5,
                gradcam_provenance='gradcam-provenance.json',
                files={str(p.relative_to(OUT)): sha(p) for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'})
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'{len(selectable)} saved observations; five Grad-CAM figures; {len(requests)} local export requests.')
