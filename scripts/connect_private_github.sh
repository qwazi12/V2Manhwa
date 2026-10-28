#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if ! command -v gh >/dev/null 2>&1; then
  echo 'GitHub CLI is required: https://cli.github.com/' >&2; exit 127
fi
if ! gh auth status >/dev/null 2>&1; then
  echo 'Sign into GitHub CLI with gh auth login before connecting a new repo.' >&2; exit 2
fi
if [[ -n "$(git remote)" ]]; then
  echo 'This repo already has a remote. Review it manually; no changes made.' >&2; exit 3
fi
printf 'Create a NEW PRIVATE GitHub repository from this project? [yes/NO]: '
read -r answer
[[ "$answer" == 'yes' ]] || { echo 'Cancelled'; exit 0; }
gh repo create flamingo-next-studio --private --source=. --remote=origin
git push -u origin main
git push -u origin codex/phase0-foundation
printf 'New private repo connected. Check: git remote -v\n'
