"""Export read-only API views and already-saved predictions; never run inference."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'auralis-front/public/demo'
OUT.mkdir(parents=True, exist_ok=True)
BASE = 'http://localhost:8000'
READ_ROUTES = ['/api/images/list', '/api/stats', '/api/benchmark', '/api/experiments',
               '/api/results-comparison?protocol=mc', '/api/results-comparison?protocol=deterministic',
               '/api/polarity-series?limit=48', '/api/agents/full-report']
requests = []

def read(path):
    # All callers below are enumerated read-only metadata/image routes.
    assert not any(x in path for x in ['predict', 'explain', 'faithfulness', 'upload'])
    requests.append(path)
    with urlopen(BASE + path, timeout=120) as response:
        return response.read()

responses = {route: json.loads(read(route)) for route in READ_ROUTES}
for experiment in responses['/api/experiments']:
    route = '/api/experiments/' + quote(experiment['metadata_file'])
    responses[route] = json.loads(read(route))

source = ROOT / 'auralis-back/reports/phase17_coronium_v3_1/http_parity.json'
full_source = ROOT / 'auralis-back/reports/phase16_coronium_v3_1/live-http.json'
saved = json.loads(source.read_text())
full = json.loads(full_source.read_text())
filenames = {sample['filename'] for sample in saved['comparisons']}
catalog = responses['/api/images/list']
selectable = [image for image in catalog['images'] if image['filename'] in filenames]
assert len(selectable) == len(filenames) == 11
responses['/demo/selectable-images'] = {'images': selectable, 'total': len(selectable)}

for sample in saved['comparisons']:
    filename, value = sample['filename'], sample['http_api']
    if filename == full['sample']:
        prediction = full['prediction']
        assert prediction['sunspot_index'] == value
    else:
        # Same documented internal thresholds; no confidence/noise values invented.
        level, label, symbol, color = ('Low', 'Low / Normal Activity', 'C', '#22c55e') if value < 1.41 else (
            ('Medium', 'Medium / Moderate Activity', 'M', '#f97316') if value < 1.75 else
            ('High', 'High / High Activity', 'X', '#ef4444'))
        prediction = {key: full['prediction'][key] for key in ['model_name', 'model_version', 'input_contract', 'target_contract', 'output_units', 'model_status', 'prediction_method']}
        prediction.update(sunspot_index=value, risk_level=level, confidence=None, uncertainty=None,
                          classification={'level': level, 'label': label, 'flare_class': symbol, 'hex_color': color,
                                          'interpretation': 'Historical internal activity bands; not GOES flare classes'})
    for prefix in ['predict', 'predict-dual']:
        responses[f'/api/{prefix}/{quote(filename)}'] = prediction
    for kind in ['images', 'aia']:
        target = OUT / kind / (filename + '.png')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(read(f'/api/{kind}/{quote(filename)}'))

# Publish an explicit archival record, not machine-local logs or live service status.
responses['/api/logs'] = [{'filename': 'demo-archivada.txt', 'lines': [
    'Demo estática: no hay un proceso de inferencia activo.',
    '11 respuestas SI HTTP verificadas conservadas de Fase 1.7; no se recalculan.',
    'Métricas y experimentos proceden de los artefactos guardados originales.',
    'Las nuevas subidas y análisis Grad-CAM están desactivados.',
]}]
responses['/health'] = {'status': 'archived', 'version': '3.1.0', 'model_loaded': False, 'device': 'not_running'}
(OUT / 'responses.json').write_text(json.dumps(responses, ensure_ascii=False, separators=(',', ':')))
manifest = {'exported_at': datetime.now(timezone.utc).isoformat(), 'new_inferences': 0,
            'catalog_images': catalog['total'], 'selectable_saved_predictions': 11,
            'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [source, full_source]},
            'read_only_requests': requests,
            'files': {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'}}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print(f'Exported {len(responses)} saved responses, {len(selectable)} image pairs; zero inference requests.')
