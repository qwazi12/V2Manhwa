#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -d .git ]]; then
  echo 'ERROR: expected a brand-new Git repository in this folder.' >&2; exit 2
fi
CURRENT="$(git rev-parse --show-toplevel)"
if [[ "$CURRENT" != "$ROOT" ]]; then
  echo "ERROR: different Git repo root: $CURRENT" >&2; exit 2
fi
if git remote -v | grep -Ei 'qwazi12/manhwa([./]|$)|manhwa\.nodepilot\.dev|recap-studio-production' >/dev/null; then
  echo 'ERROR: old-project remote detected. Refusing to start.' >&2; exit 2
fi
if ! command -v codex >/dev/null 2>&1; then
  echo 'Codex CLI is not installed. Install with: npm i -g @openai/codex' >&2
  echo 'Then sign in and rerun ./scripts/start_codex.sh' >&2
  exit 127
fi
echo 'Starting Codex with the new-project master kickoff prompt.'
echo 'Only this NEW repo is in scope. No cloud/prod work is authorized.'
codex exec --sandbox workspace-write - < CODEX_MASTER_KICKOFF.md
