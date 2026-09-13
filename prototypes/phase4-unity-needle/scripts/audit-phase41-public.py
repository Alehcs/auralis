#!/usr/bin/env python3
"""Anonymous HTTPS fetch and deployed-file parity. Does not claim physical AR."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen, Request

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['phase41', 'phase42'], default='phase41')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
origin = 'https://auralis-phase4-needle-probe.alejandro-cornejog4.chatgpt.site/'
files = sorted(p for p in (root / 'web/dist').rglob('*') if p.is_file())

def check(path):
    name = path.relative_to(root / 'web/dist').as_posix()
    request = Request(origin + ('' if name == 'index.html' else name), headers={'User-Agent': 'Auralis-Phase41-Anonymous-Audit/1.0'})
    with urlopen(request, timeout=60) as response:
        data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        expected = path.read_bytes()
        # Sites/Cloudflare may append its browser check before </body>.
        # Keep the raw hash mismatch visible and verify the application HTML separately.
        insertion = expected.find(b'</body>')
        html_application_matches = (name == 'index.html' and insertion >= 0
            and data.startswith(expected[:insertion]) and data.endswith(expected[insertion:]))
        edge_injection = data[insertion:len(data)-len(expected[insertion:])] if html_application_matches else b''
        return {'path': name, 'status': response.status, 'final_url': response.url,
                'content_type': response.headers.get('Content-Type'), 'bytes': len(data),
                'sha256': digest, 'matches_local_build': digest == hashlib.sha256(expected).hexdigest(),
                'application_html_matches': html_application_matches,
                'edge_injected_bytes': len(edge_injection),
                'edge_cloudflare_script_observed': b'/cdn-cgi/challenge-platform/' in edge_injection}

with ThreadPoolExecutor(max_workers=4) as pool:
    records = list(pool.map(check, files))
report = {'timestamp': datetime.now(timezone.utc).isoformat(), 'url': origin,
          'cookies_or_authorization_sent': False, 'files': records,
          'verification_note': 'all_match permits a reported Cloudflare script appended to otherwise identical application HTML; assets require exact SHA-256.', 'all_match': bool(records) and all(r['status'] == 200 and (r['matches_local_build'] or (r['path'] == 'index.html' and r['application_html_matches'] and r['edge_cloudflare_script_observed'])) for r in records),
          'physical_qr_scan_verified': False, 'physical_ar_verified': False}
(root / 'evidence' / args.phase / 'public-http-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'files': len(records), 'all_match': report['all_match'], 'cookies_or_authorization_sent': False}))
raise SystemExit(0 if report['all_match'] else 1)
