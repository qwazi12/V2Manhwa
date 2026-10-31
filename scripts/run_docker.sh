#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Docker Desktop is required.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 is required to initialize local keys.' >&2; exit 1; }
python3 scripts/setup_local.py
# Refuse to claim another application's host ports. Existing containers of this project are reusable.
for mapping in 'web:3000' 'api:8000'; do
  service="${mapping%:*}"
  port="${mapping#*:}"
  owned=$(bash scripts/docker_local.sh compose -f compose.yaml -f compose.app.yaml ps -q "$service")
  if [[ -z "$owned" ]] && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port belongs to another process; stop its owner before starting this studio." >&2
    exit 1
  fi
done
bash scripts/docker_local.sh compose -f compose.yaml -f compose.app.yaml build
python3 scripts/compose_start.py
set -a
source .env.local
set +a
for ((attempt=0; attempt<60; attempt++)); do
  if python3 - <<'CHECK'
import json,urllib.request
with urllib.request.urlopen('http://127.0.0.1:3000/api/v1/healthz',timeout=2) as response:
    assert json.load(response)['service']=='v2manhwa-local'
CHECK
  then
    printf '\nStudio: http://127.0.0.1:3000\nLocal studio access key: %s\n' "$FNS_LOCAL_DEV_KEY"
    echo 'The local containers keep running after this terminal closes.'
    echo 'Stop them with: bash scripts/docker_local.sh compose -f compose.yaml -f compose.app.yaml stop'
    exit 0
  fi
  sleep 1
done
echo 'The local stack did not become ready. Inspect bash scripts/docker_local.sh compose -f compose.yaml -f compose.app.yaml logs.' >&2
exit 1
