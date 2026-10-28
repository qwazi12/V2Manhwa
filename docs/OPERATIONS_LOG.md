# Operations log (append only)

## 2026-10-28 — Initial bootstrap
- Extracted and copied all 16 design package files into an independent folder.
- Initialized a fresh local Git repository with no remote; existing repo was never cloned or touched.
- Added local-only backend, frontend shell, tests, CI stub and startup script.
- No cloud resources, provider calls, publication, production data access or deployments.
- Run `make test`, `make check-contracts`, and `make test-media` to obtain actual local evidence.

## 2026-10-28 — Independent local build checkpoint

- Read supplied handoff and inspected starter. New remote qwazi12/V2Manhwa was empty; clone created under this chat workspace, branch feature/phase0-local-studio.
- Created new Compose network, PostgreSQL volume and MinIO volume under v2manhwa-local. Did not inspect or mutate the old repository, cloud apps, media, credentials or runtime state.
- Initial chosen PostgreSQL port 55432 was occupied. Docker could not bind; a subsequent manual migration command attempted that port and was denied authentication as the new fns_local user. No data was read or changed. Corrected ports, made setup fail on dependency startup failure and verified the named independent container before migration. Initial MinIO image registries were unavailable; source build and volume ownership repair resolved startup.
- Tests passed: 11 Python tests (security, real database/storage, concurrency, restart, budget, isolation, contracts and migration). Reference contracts: 48 paths / 22 AI definitions / 25 stages. FFmpeg generated and fully decoded tiny synthetic A/V. Frontend build and typecheck passed; final post-edit results below.
- Browser: entered local key without printing it to chat, created Beyond the Last Horizon, observed queued → review and loaded private SVG. No content or external-provider credential imported.
- npm mirror audit endpoint was unavailable; explicit official npm audit succeeded with 0 production dependency vulnerabilities.
- Real provider cost: $0. No cloud services, paid calls, scraping, OAuth, uploads, Drive copies or publishing actions.
- Incomplete: private-repository setting, production identity, full schema/outbox/storage ingestion, independent staging/restore and future FNS product phases. No deployment or main merge.
- Final local validation: 11/11 Python tests passed with separate fns_test database and v2manhwa-synthetic-test bucket. Typecheck and production build passed after response-model/type generation and formatting. Launcher safely reused this existing studio and returned success. Desktop and mobile DOM checks confirmed loaded preview and no horizontal overflow.
- Added runtime OpenAPI drift check: final suite 12/12 passed. A disposable database restored from a dump of the independent local database contained the expected 1 synthetic job, then was removed. This is local restore evidence only; it does not meet staging disaster-recovery acceptance.
