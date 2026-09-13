#!/usr/bin/env python3
"""Reversible local rollback. Default is a dry run; refuses to overwrite later edits."""
from pathlib import Path
import argparse,hashlib,json,shutil
p=Path(__file__).resolve().parent;web=p.parents[1]/'web'
a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args()
expected=json.loads((p/'final-source-hashes.json').read_text())
changed=[f for f,h in expected.items() if not (web/f).is_file() or hashlib.sha256((web/f).read_bytes()).hexdigest()!=h]
if changed:raise SystemExit('Refusing to overwrite edits made after Phase7.4: '+', '.join(changed))
for f in expected:
 source=p/('baseline/capture.mjs' if f=='dev/phase72-capture.mjs' else 'baseline/'+f)
 if source.read_bytes()==(web/f).read_bytes():continue
 print(('Restore ' if args.apply else 'Would restore ')+f)
 if args.apply:shutil.copy2(source,web/f)
if not args.apply:print('Dry run only. --apply restores the preserved Phase7.3 sources; no git operation.')
