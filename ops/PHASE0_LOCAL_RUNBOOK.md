# Local foundation runbook

## Startup / shutdown

Run `./start-studio.command` from the new checkout. It installs pinned dependencies, starts independent Compose services, applies migration `0001`, initializes a private bucket and launches API, worker and Next.js. It prints a local owner access key. Open http://127.0.0.1:3000 and enter it. A pre-existing listener on web/API ports stops startup. Failed Docker startup stops migration. Ctrl+C terminates the three app processes; database and object volumes remain available for restart.

`start-codex.command` remains an optional launcher for another engineering session. It is not needed while working with Codex in this chat.

The services use only `v2manhwa-local` Compose resources, database `fns_local` on port 56473, object store on 59473 and a private synthetic bucket. Test fixtures use `fns_test` only. Never substitute an existing app database or storage endpoint. Application settings refuse nonlocal infrastructure and nonlocal environments.

## Verification

1. `./scripts/prepare_test_db.sh` creates the isolated test database through the named Compose container.
2. `make test` runs real PostgreSQL/MinIO integration tests, local security/isolation checks and upgrade/downgrade/upgrade on the disposable test database.
3. `make check-contracts` validates future design contracts. `PYTHONPATH=api .venv/bin/python scripts/export_runtime_contract.py` exports the implemented API; `npm --prefix web run generate:api` generates TS interfaces.
4. `make test-media` requires FFmpeg and tests a one-second synthetic fixture, not a product export.
5. `npm --prefix web run build` validates the production frontend build. Avoid running this while Next dev is using the same `.next` directory.

### Browser smoke scenario (exercised locally on 2026-10-28)

- Anonymous page displays local sign-in. Enter launcher key; dashboard starts with actual database counts.
- New synthetic episode → enter title → create. UI shows QUEUED, then REVIEW after the separate worker processes it.
- Select the episode. Original SVG preview loads through a session-bound signed API URL. Inspect events and SHA-256.
- Search by title, use state filters, open Quality Director and Operations; no placeholder control submits real source data or publishes content.
- Resize to 390×844: workspace tabs and image preview remain usable, with no horizontal overflow.
- Sign out; API rejects the revoked session. Signing in again shows persisted jobs. A full new API instance with the prior session was also tested automatically.

Screenshots: `output/playwright/control-tower.png`, `episode-preview-desktop.png`, `episode-preview-mobile.png` (ignored local evidence).

## Known boundaries

- Authentication is **local owner access only**, not production OIDC, MFA or multi-role authorization. HTTP cookie `Secure=false` is restricted to loopback; do not expose this app through a tunnel or deploy it.
- A mock reservation is 2 units, daily cap 100. Units are not USD. The cap counts reservations, including cancelled/failed work, conservatively until the next UTC day. Every fake response costs $0.
- Jobs are queued directly in PostgreSQL; events commit with state transitions for audit. A general event bus/outbox delivery engine is not implemented.
- Object store uses local-only development credentials. Generated owner/signing keys stay in ignored `.env.local`. Never reuse these settings for cloud services.
- Worker operation is bounded below the 30-second lease; retries after process death stop after three claims. There is no live model retry or long-running renderer heartbeat yet.
- No source uploads, ZIP processing, antivirus, external fetcher, real chapter rights review, voice or video production.
- No cloud staging, restore drill, deployment or repository visibility change was performed.
