#!/bin/sh
set -eu
phase42_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
UNITY_EDITOR=${UNITY_EDITOR:-/Applications/Unity/Hub/Editor/6000.3.17f1/Unity.app/Contents/MacOS/Unity}
if [ ! -x "$UNITY_EDITOR" ]; then echo 'Unity editor not found; set UNITY_EDITOR.' >&2; exit 2; fi
mkdir -p "$phase42_root/evidence/phase42"
phase42_stamp=$(date -u +%Y%m%dT%H%M%SZ)
"$UNITY_EDITOR" -batchmode -projectPath "$phase42_root/unity" -executeMethod Phase4Probe.BuildAndExport -logFile "$phase42_root/evidence/phase42/unity-export-$phase42_stamp.log"
python3 "$phase42_root/scripts/verify-unity-export.py"
cd "$phase42_root/web"
if [ ! -d node_modules ]; then npm ci; fi
npm test
npm run build
echo 'Real export built. Next: npm run dev and open http://localhost:5184/?scene=unity. Browser and mobile validation remain required.'
