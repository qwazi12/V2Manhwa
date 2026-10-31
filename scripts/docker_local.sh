#!/usr/bin/env bash
# Project-scoped anonymous client for public base images; never reads account auth.
set -euo pipefail
cd "$(dirname "$0")/.."
docker_socket=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
case "$docker_socket" in unix://*) ;; *) echo 'The local studio requires a local Unix Docker socket.' >&2; exit 1;; esac
python3 - <<'PY'
import json,os,tempfile
from pathlib import Path
folder=Path('work/docker-anonymous');folder.mkdir(parents=True,exist_ok=True)
config={'auths':{}}
plugins=Path('/Applications/Docker.app/Contents/Resources/cli-plugins')
if plugins.is_dir():config['cliPluginsExtraDirs']=[str(plugins)]
content=json.dumps(config);target=folder/'config.json'
if not target.exists() or target.read_text()!=content:
    with tempfile.NamedTemporaryFile(mode='w',dir=folder,delete=False) as file:
        file.write(content);temporary=file.name
    os.replace(temporary,target)
PY
exec env DOCKER_CONFIG="$PWD/work/docker-anonymous" DOCKER_HOST="$docker_socket" docker "$@"
