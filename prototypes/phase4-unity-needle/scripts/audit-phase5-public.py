#!/usr/bin/env python3
"""Anonymous HTTPS parity audit for every route of the isolated Site."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/'


def check(path):
    name=path.relative_to(ROOT/'web/dist').as_posix()
    url=ORIGIN+('' if name=='index.html' else name[:-10] if name.endswith('/index.html') else name)
    with urlopen(Request(url,headers={'User-Agent':'Auralis-Phase5-Anonymous-Audit/1.0'}),timeout=45) as response:
        body=response.read(); expected=path.read_bytes()
        exact=hashlib.sha256(body).digest()==hashlib.sha256(expected).digest()
        pos=expected.find(b'</body>')
        matching_html=name.endswith('.html') and pos>=0 and body.startswith(expected[:pos]) and body.endswith(expected[pos:])
        addition=body[pos:len(body)-len(expected[pos:])] if matching_html else b''
        edge=matching_html and b'/cdn-cgi/challenge-platform/' in addition
        return {'path':name,'status':response.status,'url':response.url,
            'bytes':len(body),'content_type':response.headers.get('Content-Type'),
            'sha256':hashlib.sha256(body).hexdigest(),'exact_build_match':exact,
            'application_html_match':matching_html,'cloudflare_injection_bytes':len(addition),
            'cloudflare_script':edge,'passed':response.status==200 and (exact or edge)}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'evidence/phase5/public-http-verification.json')
    parser.add_argument('--route',default='phase5/')
    args=parser.parse_args()
    paths=sorted(p for p in (ROOT/'web/dist').rglob('*') if p.is_file())
    with ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(check,paths))
    report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'url':ORIGIN+args.route,
        'cookies_or_authorization_sent':False,'all_match':all(r['passed'] for r in records),
        'files':records,'physical_scan_or_ar_test':False,
        'note':'Asset hashes must match exactly; application HTML permits only the separately recorded Cloudflare addition before the closing body.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'all_match':report['all_match'],'files':len(records),'anonymous':True}))
    raise SystemExit(0 if report['all_match'] else 1)
