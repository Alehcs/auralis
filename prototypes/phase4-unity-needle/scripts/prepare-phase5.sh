#!/bin/sh
set -eu
phase5_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
phase5_editor=${UNITY_EDITOR:-/Applications/Unity/Hub/Editor/6000.3.17f1/Unity.app/Contents/MacOS/Unity}
python3 "$phase5_root/scripts/build-phase5-assets.py"
"$phase5_editor" -batchmode -projectPath "$phase5_root/unity" -executeMethod Phase5Solar.BuildAndExport -logFile "$phase5_root/evidence/visual-polish/unity-export-repeat.log"
python3 "$phase5_root/scripts/build-phase5-assets.py" --check
python3 "$phase5_root/scripts/verify-phase5.py"
cd "$phase5_root/web"
npm test
npm run build
