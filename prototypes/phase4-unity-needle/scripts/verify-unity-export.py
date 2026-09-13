#!/usr/bin/env python3
"""Verify export structure and recorded hash; never certify visual parity or AR."""
import hashlib
import json
from pathlib import Path
import struct
import sys

root = Path(__file__).resolve().parents[1]
model = root / 'web/public/unity/Phase4Probe.glb'
evidence = model.with_name('export-evidence.json')
if not model.exists() or not evidence.exists():
    sys.exit('PENDING: run the Unity editor export. No genuine Unity GLB/evidence exists.')
data = model.read_bytes()
magic, version, length = struct.unpack_from('<4sII', data)
if magic != b'glTF' or version != 2 or length != len(data):
    sys.exit('FAIL: invalid GLB header')
chunk_length, chunk_type = struct.unpack_from('<II', data, 12)
if chunk_type != 0x4E4F534A:
    sys.exit('FAIL: missing JSON chunk')
gltf = json.loads(data[20:20+chunk_length])
names = {node.get('name') for node in gltf.get('nodes', [])}
required = {'PlacementRoot','ProbeObject','Cube20cm','Main Camera'}
if not required.issubset(names):
    sys.exit('FAIL: missing nodes: ' + str(required-names))
meta = json.loads(evidence.read_text())
sha = hashlib.sha256(data).hexdigest()
if meta['sha256'] != sha or meta['bytes'] != len(data) or meta['exporterVersion'] != '5.1.12':
    sys.exit('FAIL: export provenance metadata mismatch')
if not gltf.get('meshes'):
    sys.exit('FAIL: no exported mesh')
for record in gltf.get('buffers', []) + gltf.get('images', []):
    uri = record.get('uri')
    if uri and not uri.startswith('data:') and not (model.parent / uri).is_file():
        sys.exit('FAIL: missing external resource: ' + uri)
report = {'status':'structure_and_recorded_hash_verified','sha256':sha,'bytes':len(data),'unityVersion':meta['unityVersion'],'generator':gltf.get('asset',{}).get('generator'),'extensionsUsed':gltf.get('extensionsUsed',[]),'nodes':sorted(x for x in names if x),'visual_parity_verified':False,'ar_verified':False}
(root/'evidence/unity-glb-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
