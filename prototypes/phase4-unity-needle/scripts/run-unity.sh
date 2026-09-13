#!/bin/sh
set -eu
phase4_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
: "${UNITY_EDITOR:?Set UNITY_EDITOR to the licensed Unity 6.3 editor executable}"
if [ ! -x "$UNITY_EDITOR" ]; then echo 'Unity editor executable not found' >&2; exit 2; fi
"$UNITY_EDITOR" -batchmode -projectPath "$phase4_root/unity" -executeMethod Phase4Probe.BuildAndExport -logFile "$phase4_root/evidence/unity-export.log"
