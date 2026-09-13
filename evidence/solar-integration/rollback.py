"""Guarded rollback of this integration only; defaults to a dry run."""
import argparse
import hashlib
import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
root = evidence.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
parser.add_argument('--mount-only', action='store_true')
args = parser.parse_args()
entries = json.loads((evidence / 'rollback-manifest.json').read_text())
if args.mount_only:
    entries = [e for e in entries if e['path'] == 'auralis-front/src/features/dashboard/dashboard-page.tsx']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

# Validate every target and baseline before any mutation.
for entry in entries:
    target = root / entry['path']
    if digest(target) != entry['after']:
        raise SystemExit(f"STOP: later changes or missing file: {entry['path']}. Nothing restored.")
    if entry['before'] and digest(evidence / 'baseline' / entry['path']) != entry['before']:
        raise SystemExit(f"STOP: baseline mismatch: {entry['path']}. Nothing restored.")
for entry in entries:
    print(('RESTORE ' if entry['before'] else 'REMOVE ') + entry['path'])
if args.apply:
    for entry in entries:
        target = root / entry['path']
        if entry['before']:
            target.write_bytes((evidence / 'baseline' / entry['path']).read_bytes())
        else:
            target.unlink()
    print('Applied. Evidence retained. Rebuild the frontend before using it.')
else:
    print('Dry run only. Pass --apply to perform these changes.')
