"""Bound the local Engine start operation without restarting Docker Desktop."""
import os
import argparse
from pathlib import Path
import signal
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--infra-only',action='store_true')
args=parser.parse_args()
command=['bash','scripts/docker_local.sh','compose','-f','compose.yaml']
if not args.infra_only:command+=['-f','compose.app.yaml']
command+=['up','-d']
process=subprocess.Popen(command,cwd=root,start_new_session=True)
try:
    sys.exit(process.wait(timeout=120))
except subprocess.TimeoutExpired:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()
    print('Docker Engine did not finish starting this studio within 120 seconds. '
          'Its project data volumes are preserved. Restart Docker Desktop, then run '
          './start-studio-docker.command again. No automatic global restart was attempted.',file=sys.stderr)
    sys.exit(1)
