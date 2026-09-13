#!/usr/bin/env python3
"""Publish only the frozen Phase2/3 scientific context. No network or inference."""
import argparse, hashlib, json
from datetime import datetime
from pathlib import Path

P=Path(__file__).resolve().parents[1];ROOT=P.parents[1];BACK=ROOT/'auralis-back'
OUT=P/'web/public/phase7';EVIDENCE=P/'evidence/phase7'
def sha(b):return hashlib.sha256(b).hexdigest()
def time(t):return datetime.fromisoformat(t.replace('Z','+00:00'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    contract_bytes=(BACK/'reports/phase3_temporal_model/noaa12975.sequence.v1.json').read_bytes()
    c=json.loads(contract_bytes);refs={a['id']:a for a in c['artifacts']}
    sequence_bytes=(P/'web/public/phase6/sequence.json').read_bytes();seq=json.loads(sequence_bytes)
    assert seq['contract_sha256']==sha(contract_bytes)
    assert [e['state'] for e in seq['entries']]==c['states']
    files={};sources={};states=[]
    def source(ref):
        a=refs[ref];raw=(BACK/a['path']).read_bytes();assert sha(raw)==a['sha256'],ref
        name=Path(a['path']).name
        if ref not in sources:
            files['sources/'+name]=raw
            sources[ref]={**a,'snapshot_url':'/phase7/sources/'+name}
        return raw.decode().splitlines()
    for s in c['states']:
        r=s['observation']['region_context'];loc=r['location']
        lines=source(loc['source_ref']);assert lines[loc['source_line']-1].strip()==loc['raw_line']
        fields=loc['raw_line'].split();assert fields[0]=='2975' and fields[1]==loc['reported'] and fields[-1]==r['magnetic_type'] and float(fields[3])==r['area_millionths_solar_hemisphere']
        source(r['harp_source_ref'])
        assert any(line.split()==['8088','12975,12976,12977,12984'] for line in source(r['harp_source_ref']))
        assert time(loc['valid_utc'])<time(s['observation']['time']['record_utc'])<time(loc['issued_utc'])
        states.append({'id':s['id'],'record_utc':s['observation']['time']['record_utc'],'region_context':r})
    for e in c['events']:
        lines=source(e['source_ref']);assert lines[e['source_line']-1].strip()==e['raw_line']
        assert e['goes_class'] in e['raw_line'] and e['raw_line'].split()[-1]=='2975'
        assert time(e['start_utc'])<=time(e['peak_utc'])<=time(e['end_utc'])
        before=[s for s in states if time(s['record_utc'])<=time(e['peak_utc'])]
        after=[s for s in states if time(s['record_utc'])>time(e['peak_utc'])]
        relation=e['temporal_relation']
        assert relation['preceding_state_id']==before[-1]['id']
        assert relation['following_state_id']==(after[0]['id'] if after else None)
        assert relation['captured_by_state_id'] is None
        assert relation['seconds_after_preceding_state']==(time(e['peak_utc'])-time(before[-1]['record_utc'])).total_seconds()
    assert len(c['events'])==6
    x=next(e for e in c['events'] if e['goes_class']=='X1.3');assert x['temporal_relation']['seconds_after_preceding_state']==63367
    # Source files above are unmodified public text snapshots already in Phase2.
    result={'schema_version':'auralis.phase7.v1','contract_sha256':sha(contract_bytes),
            'sequence_sha256':sha(sequence_bytes),'states':states,'events':c['events'],
            'sources':list(sources.values()),'event_catalog_scope':c['event_catalog_scope'],
            'timeline_basis':'UTC; HMI record time and independent GOES peak time',
            'generator_sha256':sha(Path(__file__).read_bytes())}
    files['context.json']=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
    files['context-evidence.json']=(json.dumps({'context_sha256':sha(files['context.json'])},indent=2)+'\n').encode()
    for name,raw in files.items():
        f=OUT/name
        if args.check:assert f.read_bytes()==raw,name
        else:f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
    baseline=json.loads((EVIDENCE/'protected-before.json').read_text());assert all(sha((ROOT/n).read_bytes())==h for n,h in baseline.items())
    report={'passed':True,'source':'frozen Phase2/3 only','states':len(states),'events':len(c['events']),
            'source_snapshots':len(sources),'protected_files_unchanged':len(baseline),
            'x13_seconds_after_state5':63367,'output_hashes':{n:sha(b) for n,b in files.items()}}
    (EVIDENCE/'context-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
