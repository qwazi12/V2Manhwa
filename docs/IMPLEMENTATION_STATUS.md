# Implementation status — 2026-10-28

**Local foundation implemented and exercised. Phase 0 is NOT complete.** No production deployment or full platform completion is claimed.

| Component | Status | Evidence / remaining boundary |
|---|---|---|
| Independent V2Manhwa checkout | IMPLEMENTED | Initially empty target, new history; remote differs from prohibited project. Target observed public, so private-repository gate remains unmet. |
| Next.js studio | LOCAL VALIDATED | Production build/types; browser sign-in → create → private preview; desktop and 390px mobile screenshots. |
| FastAPI modular local API | LOCAL VALIDATED | Real PostgreSQL/MinIO TestClient tests; protected runtime schema and generated TypeScript types. |
| Local owner authentication | LOCAL VALIDATED, LIMITED | Revocation, expiry checks, HttpOnly/SameSite cookie, CSRF/Origin and rate limits for one process. OIDC/MFA/editor roles/HTTPS deployment deferred. |
| Dedicated PostgreSQL | LOCAL VALIDATED, SLICE ONLY | Persistent jobs/sessions/events/budgets and migration 0001. Fresh upgrade/downgrade/upgrade tested. Full blueprint SQL is not applied. |
| Private object store / signed image | LOCAL VALIDATED, SLICE ONLY | Source-built MinIO; original SVG; checksum, tamper, expiry and different-session rejection. Upload/archive/antivirus and MP4 absent. |
| Jobs / worker / event records | LOCAL VALIDATED, SLICE ONLY | Transactional queue and events, concurrent claims/idempotency, revision checks, cancellation, lease expiry/recovery and stale-worker fencing. General outbox delivery and long render leases absent. |
| Fake model / mock budget | LOCAL VALIDATED, LIMITED | Strict response validation, reservation enforcement, atomic daily mock cap. No paid adapters or dollar accounting. |
| CI | CONFIGURED | Runs tests, contract drift, web build and FFmpeg fixture with separate local services. Hosted execution recorded separately after push. |
| Research/story/TTS/episode rendering | DESIGNED ONLY | UI labels planned modules; no provider connection or real episode export. |
| Staging / recovery / production | NOT IMPLEMENTED | Needs independent approved resource inventory, production identity, backups and restore exercise. |
| Publishing/Drive/autopilot/paid providers | DISABLED | No adapters or credentials; server refuses enabling flags. |

Verification: 12 tests passed, including PostgreSQL/MinIO and migration tests; final counts are recorded in `docs/OPERATIONS_LOG.md`. Static reference contract validation passed; synthetic FFmpeg render/decode passed; npm production dependency audit reported zero vulnerabilities using the official npm registry. This does not substitute for a full supply-chain/security audit.

Next prerequisite: finish the remaining auth/storage/job acceptance gates and independent staging/resource decisions before calling any Phase 0 ticket complete. Subsequent source-ingestion phases remain on the original FNS roadmap.
