#!/usr/bin/env python3
"""Deterministic display-only HMI disk -> existing Unity sphere UV atlas.

No WCS, radial-field inference, spot identification or scientific interpolation.
The phase6 manifest and its fifteen linear maps remain frozen.
"""
import argparse, hashlib, io, json, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, binary_fill_holes, gaussian_filter, map_coordinates

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[1]
BACK = ROOT / 'auralis-back'
PUBLIC = P / 'web/public/phase6'
EVIDENCE = P / 'evidence/phase61'

def sha(b): return hashlib.sha256(b).hexdigest()

def fit_disk(x):
    # The processed arrays retain a sharp zero-valued exterior. Filling internal
    # zeros prevents real neutral-polarity pixels from becoming limb candidates.
    support = binary_fill_holes(x != 0)
    rows, cols = np.where(support & ~binary_erosion(support))
    cx, cy, k = np.linalg.lstsq(np.c_[2*cols, 2*rows, np.ones(len(rows))], cols**2+rows**2, rcond=None)[0]
    radius = np.sqrt(k+cx*cx+cy*cy)
    residual = np.abs(np.hypot(cols-cx, rows-cy)-radius)
    assert 245 < radius < 256 and residual.max() < 2
    return {'cx':float(cx), 'cy':float(cy), 'radius':float(radius),
            'edge_residual_p95_px':float(np.percentile(residual,95)),
            'edge_residual_max_px':float(residual.max()), 'method':'circle_fit_zero_exterior_filled_support'}

def uv_geometry(u, v):
    # Verified against actual exported POSITION and TEXCOORD_0, not assumed WCS.
    # UnityGLTF flips Unity X and V. Front camera is at glTF -Z, screen right -X.
    theta = np.pi*v; phi = 2*np.pi*u
    return np.sin(theta)*np.cos(phi), np.cos(theta), np.sin(theta)*np.sin(phi)

def verify_glb_uv():
    raw=(P/'web/public/phase5/Phase5Solar.glb').read_bytes()
    n=struct.unpack_from('<I',raw,12)[0]; g=json.loads(raw[20:20+n]);binary=raw[28+n:]
    node=next(x for x in g['nodes'] if x['name']=='IllustrativeSphere')
    primitive=g['meshes'][node['mesh']]['primitives'][0]
    def array(name,size):
        a=g['accessors'][primitive['attributes'][name]];v=g['bufferViews'][a['bufferView']]
        return np.ndarray((a['count'],size),dtype='<f4',buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*4),4))
    pos=array('POSITION',3);uv=array('TEXCOORD_0',2)
    right,up,z=uv_geometry(uv[:,0],uv[:,1])
    predicted=np.stack([-right,up,z],axis=-1)*.42
    error=float(np.max(np.abs(predicted-pos))); assert error<1e-6,error
    return {'sha256':sha(raw),'vertices':len(pos),'max_position_error':error,'screen_right':'-X','screen_up':'+Y','data_hemisphere':'Z<0'}

def render(x, disk, base):
    h,w=base.shape[:2]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    right,up,z=uv_geometry(u,v)
    cols=disk['cx']+disk['radius']*right; rows=disk['cy']-disk['radius']*up
    plus=np.maximum(x,0);minus=np.maximum(-x,0)
    # A common transfer for ALL dates; no per-date normalization and no SI input.
    p=gaussian_filter(np.maximum(plus-.04,0),1.15)
    m=gaussian_filter(np.maximum(minus-.04,0),1.15)
    magnitude=p+m
    halo=gaussian_filter(magnitude,3)
    def sample(a): return map_coordinates(a,[rows,cols],order=1,mode='constant',cval=0,prefilter=False)
    pp,mm,hh=sample(p),sample(m),sample(halo)
    # Fade out only in the last ~1.1 input pixels near the limb (mu < .095).
    # Back remains the SAME fixed illustration, never a mirrored HMI disk.
    mu=np.clip(-z/.095,0,1);coverage=mu*mu*(3-2*mu)
    strength=1-np.exp(-7*(pp+mm))
    diffuse=1-np.exp(-5*hh)
    polarity=pp/(pp+mm+1e-12)
    rgb=base.astype(float)/255
    # Dark magnetic concentrations + warm polarity rims are visual metaphors,
    # explicitly NOT observed sunspots, temperature, plasma or field lines.
    core=np.array([.105,.026,.032])[None,None,:]
    positive=np.array([1.,.79,.36]);negative=np.array([1.,.29,.12])
    tint=negative+(positive-negative)*polarity[:,:,None]
    glow=diffuse*coverage*.82
    rgb=rgb*(1-glow[:,:,None])+tint*glow[:,:,None]
    dark=strength*coverage*.94
    rgb=rgb*(1-dark[:,:,None])+core*dark[:,:,None]
    out=np.rint(np.clip(rgb,0,1)*255).astype('uint8')
    assert np.array_equal(out[z>=0],base[z>=0])
    return out, {'nonzero_activity_texels':int(np.count_nonzero((strength>.05)&(z<0))),
                 'back_exactly_unchanged':True}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    seqbytes=(PUBLIC/'sequence.json').read_bytes();seq=json.loads(seqbytes)
    # Use the original 2048x1024 baked illustration as a fixed baseline.
    # Texture dimensions are fixed across states. Original assets untouched.
    base=np.array(Image.open(P/'unity/Assets/Phase5/solar-illustration.png').convert('RGB').resize((2048,1024),Image.Resampling.LANCZOS))
    files={};entries=[];checks=[]
    for entry in seq['entries']:
        s=entry['state'];ref=entry['source'];raw=(BACK/ref['path']).read_bytes();assert sha(raw)==ref['sha256']
        x=np.load(io.BytesIO(raw),allow_pickle=False);assert x.shape==(512,512) and np.isfinite(x).all()
        disk=fit_disk(x);atlas,check=render(x,disk,base)
        buf=io.BytesIO();Image.fromarray(atlas).save(buf,format='PNG')
        name=f'assets/{s["id"]}/solar-activity.png';files[name]=buf.getvalue()
        entries.append({'id':s['id'],'source_sha256':ref['sha256'],'disk':disk,'solar':{'url':'/phase6/'+name,'sha256':sha(files[name]),'width':2048,'height':1024,'origin':'gltf_uv_top_left','kind':'magnetic_activity_recreation'}})
        checks.append({'id':s['id'],**check,'disk':disk})
    manifest={'schema_version':'auralis.phase61.v1','sequence_sha256':sha(seqbytes),'contract_sha256':seq['contract_sha256'],
      'glb':verify_glb_uv(),'entries':entries,'recipe':{'script_sha256':sha(Path(__file__).read_bytes()),
      'source':'float32 clipped normalized B_LOS; B+=max(x,0), B-=max(-x,0)',
      'projection':'orthographic_disk_to_front_hemisphere; array orientation only; no WCS',
      'transfer':'fixed threshold .04; Gaussian sigma 1.15 px per polarity; halo sigma 3 px; exp gains 7 and 5; no SI or per-date scaling',
      'back':'unchanged baked illustration; no HMI samples','spots':'not identified; dark marks are recreated magnetic concentrations',
      'transition':'260 ms graphical crossfade only; no intermediate physical state'}}
    files['activity.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    files['activity-evidence.json']=(json.dumps({'activity_sha256':sha(files['activity.json'])},indent=2)+'\n').encode()
    for name,b in files.items():
        path=PUBLIC/name
        if args.check:assert path.read_bytes()==b,name
        else:path.parent.mkdir(exist_ok=True,parents=True);path.write_bytes(b)
    baseline=json.loads((EVIDENCE/'protected-before.json').read_text())
    assert all(sha((ROOT/n).read_bytes())==h for n,h in baseline.items())
    report={'passed':True,'protected_files_unchanged':len(baseline),'states':checks,'glb_uv':manifest['glb'],'output_hashes':{n:sha(b) for n,b in files.items()},'total_png_bytes':sum(len(b) for n,b in files.items() if n.endswith('.png'))}
    EVIDENCE.mkdir(exist_ok=True,parents=True);(EVIDENCE/'asset-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'states':len(entries),'protected':len(baseline),'png_bytes':report['total_png_bytes']}))

if __name__=='__main__':main()
