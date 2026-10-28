#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Docker Desktop is required.' >&2; exit 1; }
command -v npm >/dev/null || { echo 'Node.js 20.9+ and npm are required.' >&2; exit 1; }
python3 scripts/setup_local.py
set -a
source .env.local
set +a
export PYTHONPATH="$PWD/api"
if python3 - <<'CHECK'
import json, urllib.request
try:
    for port in (3000, 8000):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/healthz', timeout=2) as response:
            assert json.load(response)['service'] == 'v2manhwa-local'
except Exception:
    raise SystemExit(1)
CHECK
then
  printf '\nStudio is already running: http://127.0.0.1:3000\nLocal studio access key: %s\n' "$FNS_LOCAL_DEV_KEY"
  exit 0
fi
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip --version >/dev/null 2>&1 || .venv/bin/python -m ensurepip
.venv/bin/python -m pip install -r requirements.lock
if [[ ! -d web/node_modules ]]; then (cd web && npm ci); fi
# Avoid claiming or stopping another application's servers.
for port in 3000 8000; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is already in use. Stop its owner or use the existing studio." >&2
    exit 1
  fi
done
docker compose up -d --build
for ((i=0; i<60; i++)); do
  if docker compose exec -T postgres pg_isready -U fns_local -d fns_local >/dev/null 2>&1; then break; fi
  sleep 1
done
# Confirm this exact Compose database is healthy before any host migration.
docker compose exec -T postgres pg_isready -U fns_local -d fns_local >/dev/null
.venv/bin/alembic -c api/alembic.ini upgrade head
for ((i=0; i<60; i++)); do
  if .venv/bin/python -c 'from flamingo_next_api.config import Settings; from flamingo_next_api.storage import Storage; Storage(Settings.load()).initialize()' 2>/dev/null; then break; fi
  if [[ "$i" == 59 ]]; then echo 'Object store did not become ready.' >&2; exit 1; fi
  sleep 1
done
mkdir -p work
# The key appears only in the local launcher terminal, never in frontend bundles/logs.
printf '\nLocal studio access key: %s\n\n' "$FNS_LOCAL_DEV_KEY"
echo 'Studio: http://127.0.0.1:3000 — press Ctrl+C to stop the API, worker and web.'
.venv/bin/python -m uvicorn flamingo_next_api.main:app --host 127.0.0.1 --port 8000 --no-access-log > work/api.log 2>&1 &
api_pid=$!
.venv/bin/python -m flamingo_next_api.worker > work/worker.log 2>&1 &
worker_pid=$!
(cd web && exec node node_modules/next/dist/bin/next dev --hostname 127.0.0.1) > work/web.log 2>&1 &
web_pid=$!
cleanup() { kill "$api_pid" "$worker_pid" "$web_pid" 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 0' INT TERM
# Check all three children, including after startup; avoid an apparently live shell
# with a dead worker. Docker dependencies remain persistent for the next launch.
while kill -0 "$api_pid" 2>/dev/null && kill -0 "$worker_pid" 2>/dev/null && kill -0 "$web_pid" 2>/dev/null; do sleep 2; done
echo 'A studio service stopped. Check work/api.log, work/worker.log and work/web.log.' >&2
exit 1
