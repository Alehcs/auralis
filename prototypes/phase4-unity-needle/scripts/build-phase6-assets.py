#!/usr/bin/env python3
"""Read the frozen temporal contract; derive display PNGs without inference or source writes."""
import argparse, hashlib, io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1]; ROOT=P.parents[1]; BACK=ROOT/'auralis-back'
sys.path.insert(0,str(BACK))
from src.processing.model_input import prepare_model_input

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    source=BACK/'reports/phase3_temporal_model/noaa12975.sequence.v1.json';c=json.loads(source.read_bytes())
    states=sorted(c['states'],key=lambda s:s['order']);assert len(states)==5
    refs={a['id']:a for a in c['artifacts']};entries=[];files={};checks=[]
    for s in states:
        ref=refs[s['observation']['magnetogram']['artifact_ref']];raw=(BACK/ref['path']).read_bytes();assert sha(raw)==ref['sha256']
        x=np.load(io.BytesIO(raw),allow_pickle=False);assert x.shape==(512,512) and x.dtype==np.float32 and np.isfinite(x).all()
        plus,minus=np.asarray(prepare_model_input(x));assert np.array_equal(plus-minus,x)
        means=[float(a.mean(dtype=np.float64)) for a in (plus,minus)]
        pol=s['derived']['polarity'];assert np.allclose(means,[pol['b_plus_mean'],pol['b_minus_magnitude_mean']],rtol=0,atol=1e-12)
        layers={}
        for name,a in [('magnetogram',np.rint((x.astype('float64')+1)*127.5)),('bplus',np.rint(plus.astype('float64')*255)),('bminus',np.rint(minus.astype('float64')*255))]:
            a=a.astype('uint8');out=io.BytesIO();Image.fromarray(a).convert('RGBA').save(out,format='PNG')
            path=f'assets/{s["id"]}/{name}.png';files[path]=out.getvalue()
            assert np.array_equal(np.array(Image.open(io.BytesIO(files[path])).convert('L')),a)
            layers[name]={'url':'/phase6/'+path,'sha256':sha(files[path]),'width':512,'height':512,'origin':'upper_left_array_row0','range':[-1,1] if name=='magnetogram' else [0,1],'unit':'dimensionless_clip400'}
        entries.append({'state':s,'layers':layers,'source':ref})
        checks.append({'id':s['id'],'filename':s['observation']['magnetogram']['filename'],'utc':s['observation']['time']['record_utc'],'si':s['observation']['target_si']['value'],'prediction':s['coronium_results']['prediction_si'],'channel_means':means,'all_pixels_verified':True})
    manifest={'schema_version':'auralis.phase6.v1','contract_sha256':sha(source.read_bytes()),'sequence_id':c['sequence_id'],'model':c['model'],'preprocessing':c['preprocessing'],'entries':entries,'limitations':c['limitations'],'visual':{'sphere':'unchanged_illustration_360','data_projection':'none','transition':'display_fade_only_no_numeric_or_magnetic_interpolation'},'generation':{'script_sha256':sha(Path(__file__).read_bytes()),'recipe':'signed=round((x+1)*127.5); plus=round(max(x,0)*255); minus=round(max(-x,0)*255); RGBA alpha255; no flips or crop'}}
    files['sequence.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    evidence={'sequence_sha256':sha(files['sequence.json']),'contract_sha256':sha(source.read_bytes()),'unity_glb_sha256':sha((P/'web/public/phase5/Phase5Solar.glb').read_bytes())}
    files['sequence-evidence.json']=(json.dumps(evidence,indent=2)+'\n').encode()
    for name,b in files.items():
        f=P/'web/public/phase6'/name
        if args.check: assert f.read_bytes()==b,name
        else:f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
    baseline=json.loads((P/'evidence/phase6/protected-before.json').read_text());changed=[n for n,h in baseline.items() if sha((ROOT/n).read_bytes())!=h];assert not changed,changed
    report={'passed':True,'states':checks,'protected_files_unchanged':len(baseline),'output_hashes':{k:sha(v) for k,v in files.items()},'last_si_declines':checks[-1]['si']<checks[-2]['si']}
    (P/'evidence/phase6/asset-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'states':len(entries),'files':len(files),'protected':len(baseline)}))
if __name__=='__main__':main()
