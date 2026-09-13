from pathlib import Path
from urllib.request import urlopen
import hashlib,json
root=Path(__file__).resolve().parents[2]
results=[]
for directory in ('phase5','phase6','phase7','assets','unity'):
    for source in (root/'prototypes/phase4-unity-needle/web/dist'/directory).rglob('*'):
        if not source.is_file():continue
        rel=source.relative_to(root/'prototypes/phase4-unity-needle/web/dist')
        with urlopen('http://localhost:5173/'+str(rel),timeout=15) as response:
            body=response.read();assert response.status==200
        assert body==source.read_bytes(), str(rel)
        results.append({'path':str(rel),'sha256':hashlib.sha256(body).hexdigest()})
(root/'evidence/solar-integration/http-assets.json').write_text(json.dumps(results,indent=2))
print(f'{len(results)} HTTP assets match the single viewer build byte for byte')
