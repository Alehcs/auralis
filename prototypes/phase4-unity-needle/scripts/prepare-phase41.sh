#!/bin/sh
# Produce a mobile build only after an actual licensed Unity export succeeds.
set -eu
phase41_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -z "${UNITY_EDITOR:-}" ]; then
  UNITY_EDITOR='/Applications/Unity/Hub/Editor/6000.3.0f1/Unity.app/Contents/MacOS/Unity'
fi
export UNITY_EDITOR
if [ ! -x "$UNITY_EDITOR" ]; then
  echo 'PENDIENTE: instalar y activar Unity 6.3 LTS en Unity Hub.' >&2
  echo 'Si ya existe otra versión 6000.3, definir UNITY_EDITOR con su ejecutable.' >&2
  exit 2
fi
sh "$phase41_root/scripts/run-unity.sh"
python3 "$phase41_root/scripts/verify-unity-export.py"
cd "$phase41_root/web"
npm ci
npm test
npm run build
echo 'Build Unity real preparado en web/dist. Revisar /?scene=unity y publicar este build antes de probar QR/AR.'
