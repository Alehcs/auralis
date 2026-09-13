#!/usr/bin/env python3
"""Read-only asset/science regression check against the pre-edit snapshot."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[1]
E = P / 'evidence/phase71'
baseline = json.loads((E / 'protected-before.json').read_text())
changed = [name for name, digest in baseline.items()
           if not (ROOT / name).is_file()
           or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
assert not changed, changed
sequence = json.loads((P / 'web/public/phase6/sequence.json').read_text())
states = [e['state'] for e in sequence['entries']]
assert len(states) == 5
assert states[4]['observation']['target_si']['value'] < states[3]['observation']['target_si']['value']
print(json.dumps({'passed': True, 'protected_files_unchanged': len(baseline),
                  'states': len(states), 'final_si_decline_preserved': True,
                  'unity_glb_sha256': hashlib.sha256((P / 'web/public/phase5/Phase5Solar.glb').read_bytes()).hexdigest()}, indent=2))
