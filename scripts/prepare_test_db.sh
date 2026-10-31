#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# No host connection: target the named independent container directly.
docker compose exec -T postgres sh -c 'psql -U fns_local -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '\''fns_test'\''" | grep -q 1 || createdb -U fns_local fns_test'
