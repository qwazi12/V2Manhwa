# Flamingo Next Studio — Codex project instructions

**THIS IS A COMPLETELY NEW APPLICATION.** Do not clone, fork, read, modify, connect, deploy, import, or use runtime resources from `qwazi12/manhwa`, `manhwa.nodepilot.dev`, or its backend. No production access. No silent cloud provisioning.

## Mandatory first action
Read `CODEX_MASTER_KICKOFF.md` **in full** and follow its *Required reading order*. Treat that document as the opening user assignment. The entire blueprint package is checked in at the repository root. Use `roadmap/BUILD_PLAN.md` for FNS-001 through FNS-055 and `qa/ACCEPTANCE_MATRIX.md` for tests.

## What exists right now
The starter includes the complete design package and a **limited, local-only Phase 0 scaffold**: Next.js shell, FastAPI demo capability endpoints, local Compose dependency configuration, offline Python/security/contract/media tests. The database is not integrated, auth is not production-ready, and no real workers, AI providers, media uploads, publishing or research sources have been implemented. Do not claim Phase 0 or any FNS ticket is completed.

## Engineering rules
- Never set a Git remote to the old repo; verify `git remote -v` before every first push.
- New repo only. Prefer small feature branches, tests, PR review and documented decisions.
- Do not auto-deploy. Never create paid resources or call paid external AI without new explicit approval.
- `PUBLISHING_ENABLED=false`, `DRIVE_AUTO_COPY_ENABLED=false`, `AUTOPILOT_MODE=OFF`, `ALLOW_PROTECTED_SOURCE_SCRAPING=false` by default and until independently authorized.
- Only original/synthetic/authorized test media; rights gate before source access and distribution.
- All new model results are untrusted data and require strict validation, provenance, budgets and review.
- No fake success. Keep `docs/IMPLEMENTATION_STATUS.md`, `docs/ISSUE_LEDGER.md`, `docs/DECISION_LOG.md`, and `docs/OPERATIONS_LOG.md` updated.
- All new content must be separately approved and reviewed before any publishing.

## Local commands
`make test`, `make test-media`, `make check-contracts`, `make e2e` run offline; `make api` runs a dev-only API; `make infra` starts local Postgres/MinIO if Docker is installed; `make web` requires npm dependencies.

**Start with FNS-001 to FNS-003, confirm isolation, then implement Phase 0 vertical slices. Use the master kickoff prompt.**
