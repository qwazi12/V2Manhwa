# Flamingo Next Studio / V2Manhwa

An independent, local manhwa production workspace. The first implemented slice is a real **synthetic job → durable queue → fake provider → private image preview** workflow, with no paid integrations or publishing.

## Run the app

Prerequisites: Docker Desktop running, Python 3.11+, Node.js 20.9+ and npm. First setup downloads dependencies and compiles the pinned MinIO source release; allow a few minutes.

```bash
./start-studio.command
```

Open **http://127.0.0.1:3000** and enter the local access key printed in that terminal. Keys are generated into ignored `.env.local` with mode 0600; they are not bundled into the frontend. Ctrl+C stops the app servers. Docker volumes persist your work.

`./start-codex.command` is the original **engineering handoff launcher**, which starts a separate Codex CLI session. It does not start the app. The implementation in this checkout follows that handoff directly.

## What works locally

- Responsive Control Tower, Episode Studio, preview review queue and Operations screens.
- Revocable local owner session, HttpOnly SameSite cookie and Origin/CSRF enforcement.
- PostgreSQL job state, idempotency, revisions, cancellation, bounded leases/recovery and transactional event records.
- Separate worker with validated deterministic fake responses and atomic mock-budget reservations.
- Private MinIO objects, content hashes and five-minute, session-bound preview signatures.
- Runtime OpenAPI, generated TypeScript contracts, database migration and integration/security tests.

The preview is an original synthetic SVG cover, **not a narrated video**. Preview review does not imply editorial approval. Real source ingestion, OCR/story intelligence, narration, video exports, publishing, production OIDC, invited users, general outbox consumers and cloud staging remain unimplemented. Phase 0 is **not complete**; see `docs/IMPLEMENTATION_STATUS.md`.

## Verify

With Docker dependencies running:

```bash
./scripts/prepare_test_db.sh
make test check-contracts test-media
npm --prefix web run typecheck
npm --prefix web run build
```

`make test` uses only the dedicated disposable `fns_test` database. `make test-media` separately renders and decodes a one-second FFmpeg fixture; it is not an episode renderer. Browser evidence and checks are documented in `ops/PHASE0_LOCAL_RUNBOOK.md`.

Ports: web 3000, API 8000, PostgreSQL 56473, private S3 59473, local storage console 59474. All bind to loopback. No cloud resources or public deployment are created.

## Specification and safety

`FLAMINGO_NEXT_BLUEPRINT.md`, `roadmap/BUILD_PLAN.md` and `qa/ACCEPTANCE_MATRIX.md` describe the larger product. `contracts/openapi.yaml` is that future product design; `contracts/local.openapi.json` is the API actually implemented here. All public publishing, Drive copying, autopilot, protected scraping and paid providers remain disabled.

The supplied GitHub target is `qwazi12/V2Manhwa`. It was empty and public when inspected. Repository privacy, production identity, cloud staging and release authorization are owner decisions; this local implementation does not claim those gates passed.
