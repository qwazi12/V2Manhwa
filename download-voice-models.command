#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 scripts/download_voice_models.py
if [[ "${1:-}" == '--docker' ]]; then
  exec bash scripts/install_voice_docker.sh
fi
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python -m pip install -r requirements-voice.lock
fi
echo 'For the container studio, also run: ./download-voice-models.command --docker'
