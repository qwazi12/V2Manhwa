#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
model_folder=$(PYTHONPATH=api python3 -c 'from flamingo_next_api.voice_models import verify; print(verify())')
compose=(bash scripts/docker_local.sh compose -f compose.yaml -f compose.app.yaml --profile voice-setup)
"${compose[@]}" create voice-models-setup
cleanup() { "${compose[@]}" rm -f voice-models-setup >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Copy only the two pinned public assets; no host-directory sharing is needed.
for filename in kokoro-v1.0.onnx voices-v1.0.bin; do
  "${compose[@]}" cp "$model_folder/$filename" "voice-models-setup:/opt/fns-models/$filename.incoming"
done
"${compose[@]}" start -a voice-models-setup
status=$("${compose[@]}" ps -a --format json voice-models-setup)
python3 -c 'import json,sys; value=json.loads(sys.argv[1]); assert value["ExitCode"]==0, "Model installer failed"' "$status"
