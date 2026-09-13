#!/usr/bin/env python3
"""Verify source -> PNG -> Unity-exported GLB and protected-file integrity."""
import hashlib
import io
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image

PROBE = Path(__file__).resolve().parents[1]
ROOT = PROBE.parents[1]
PUBLIC = PROBE / 'web/public/phase5'


def sha(p):
    return hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()


def main():
    meta = json.loads((PUBLIC / 'export-evidence.json').read_text())
    state = json.loads((PUBLIC / 'state.json').read_text())
    glb = (PUBLIC / 'Phase5Solar.glb').read_bytes()
    assert glb[:4] == b'glTF' and struct.unpack_from('<II', glb, 4) == (2, len(glb))
    assert meta['sha256'] == hashlib.sha256(glb).hexdigest() and meta['bytes'] == len(glb)
    assert meta['stateSha256'] == sha(PUBLIC / 'state.json')
    assert meta['authoringSha256'] == sha(PROBE / 'unity/Assets/Editor/Phase5Solar.cs')
    assert meta['sceneSha256'] == sha(PROBE / 'unity/Assets/Scenes/Phase5Solar.unity')
    assert meta['unityVersion'] == '6000.3.17f1' and meta['exporterVersion'] == '5.1.12'
    n = struct.unpack_from('<I', glb, 12)[0]
    g = json.loads(glb[20:20+n]); binary = glb[28+n:]
    assert g['asset']['generator'] == 'Needle Engine Unity Integration 5.1.12'
    assert not any(b.get('uri') for b in g['buffers'])
    assert not any(i.get('uri') for i in g['images'])
    nodes = {node['name']: node for node in g['nodes']}
    for name in ['Phase5Placement','SolarState','IllustrativeSphere','SubtleCorona','Layer_magnetogram','Layer_bplus','Layer_bminus','Phase5 Camera']:
        assert name in nodes, name
    for material in g['materials']:
        assert 'KHR_materials_unlit' in material.get('extensions', {}), material['name']

    def view_bytes(idx):
        v = g['bufferViews'][idx]; offset = v.get('byteOffset',0)
        return binary[offset:offset+v['byteLength']]

    def accessor(idx):
        a = g['accessors'][idx]; v = g['bufferViews'][a['bufferView']]
        count = {'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']]
        dtype = {5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
        itemsize=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],count),dtype=dtype,buffer=binary,
            offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',itemsize*count),itemsize)).copy()

    checked = {}
    for name in ['magnetogram','bplus','bminus']:
        mesh = g['meshes'][nodes['Layer_'+name]['mesh']]['primitives'][0]
        material = g['materials'][mesh['material']]
        texture_index = material['pbrMetallicRoughness']['baseColorTexture']['index']
        image_index = g['textures'][texture_index]['source']; img = g['images'][image_index]
        assert img['name'] == name and img['mimeType'] == 'image/png', img
        embedded = np.array(Image.open(io.BytesIO(view_bytes(img['bufferView']))).convert('RGBA'))
        original = np.array(Image.open(PUBLIC / 'assets' / (name+'.png')).convert('RGBA'))
        # No JPEG ringing, channel swaps, inversion, crop, transpose or mirror.
        assert np.array_equal(embedded, original), (name, np.max(np.abs(embedded.astype(int)-original.astype(int))))
        assert np.all(embedded[:,:,3] == 255)
        positions=accessor(mesh['attributes']['POSITION']); uv=accessor(mesh['attributes']['TEXCOORD_0'])
        # glTF camera at -Z looks toward +Z, so screen-right is -X; screen-top is +Y.
        # glTF texture coordinates start at top-left (v=0). Unity conversion flips X.
        screen_right=-positions[:,0]; screen_top=positions[:,1]
        assert np.corrcoef(screen_right, uv[:,0])[0,1] > .999, (name,'horizontal mirror')
        assert np.corrcoef(screen_top, uv[:,1])[0,1] < -.999, (name,'vertical mirror')
        texinfo=material['pbrMetallicRoughness']['baseColorTexture']
        transform=texinfo.get('extensions',{}).get('KHR_texture_transform',{})
        assert transform.get('scale',[1,1]) == [1,1] and transform.get('offset',[0,0]) == [0,0] and transform.get('rotation',0)==0
        checked[name]={'embedded_png_exact':True,'max_pixel_difference':0,'opaque':True,'front_uv_orientation_preserved':True}
    camera=nodes['Phase5 Camera']
    sphere=g['meshes'][nodes['IllustrativeSphere']['mesh']]['primitives'][0]
    positions=accessor(sphere['attributes']['POSITION'])
    assert np.allclose(np.linalg.norm(positions,axis=1),.42,atol=1e-5)
    assert positions[:,2].min()<-.419 and positions[:,2].max()>.419
    assert 'UnobservedBack' not in nodes and 'ReferenceBack' not in nodes
    assert not any(i['name'].startswith('no-data') for i in g['images'])
    solar=np.array(Image.open(PROBE/'unity/Assets/Phase5/solar-illustration.png'))
    assert solar.shape[:2]==(1024,2048)
    assert np.max(np.abs(solar[:,0].astype(int)-solar[:,-1].astype(int)))<=1, 'Longitude seam'
    assert np.max(np.ptp(solar[0].astype(int),axis=0))<=1 and np.max(np.ptp(solar[-1].astype(int),axis=0))<=1, 'Pole discontinuity'
    state_before=json.loads((PROBE/'evidence/visual-polish/before-state.json').read_text())
    assert state['state']==state_before['state'] and state['layers']==state_before['layers']
    polish_before=json.loads((PROBE/'evidence/visual-polish/protected-before.json').read_text())
    assert all((ROOT/name).is_file() and sha(ROOT/name)==h for name,h in polish_before.items()), 'Protected polish baseline changed'
    assert np.allclose(camera['translation'],[0,.5,-2])
    assert np.allclose(camera['rotation'],[0,1,0,0],atol=1e-6)
    # Check all baseline files, including already-dirty user files, not only Git diff.
    before=json.loads((PROBE/'evidence/phase5/protected-before.json').read_text())
    changed=[name for name,h in before.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=h]
    registry='prototypes/phase4-unity-needle/unity/ProjectSettings/NeedleExporterSceneData.asset'
    # Needle registers the new scene automatically. Permit only this exact addition;
    # the previous Phase4 registry bytes and all other project settings must match.
    registry_addition='  - Path: Assets/Scenes/Phase5Solar.unity\n    Projects:\n    - ProjectPath: ../web\n    BuilderScene: \n'
    if registry in changed:
        previous=(ROOT/registry).read_text().replace(registry_addition,'')
        assert hashlib.sha256(previous.encode()).hexdigest()==before[registry], 'Unexpected Unity registry change'
        changed.remove(registry)
    assert not changed, changed
    raw_json=json.dumps(g)
    assert '/Users/' not in raw_json and 'file://' not in raw_json
    report={'status':'passed','unity_export':meta,'self_contained_glb':True,'scientific_layers':checked,
        'source_reference_only_2d':True,'continuous_illustrative_sphere':True,'longitude_and_poles_continuous':True,'observational_state_and_maps_unchanged':True,'polish_protected_files_unchanged':len(polish_before),
        'protected_files_unchanged':len(before)-1,'protected_changes':changed,
        'allowed_unity_registry_change':'only new Phase5 scene registration; previous content hash preserved',
        'state_id':state['state']['id'],'model':state['model']['name'],'physical_mobile_ar':'not_tested'}
    (PROBE/'evidence/visual-polish/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (PROBE/'evidence/visual-polish/glb-structure.json').write_text(json.dumps(g,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
