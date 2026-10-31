# Flamingo Next Studio — Independent infrastructure and operations runbook

**Version 1.0 — New build only.** This runbook describes **new cloud projects and new credentials**. It does not authorize an actual deployment, paid provision, old service inspection, publishing, or using any credential from `qwazi12/manhwa`.

## 0. Control plane and resource naming

Recommended resource suffixes (examples, **not created**):

| Resource | New staging | New production |
|---|---|---|
| GitHub | `flamingo-next-studio`, `staging` branch/preview | Same **new** repository, protected `main` |
| Vercel | `flamingo-next-web-staging` | `flamingo-next-web` |
| Railway | `flamingo-next-staging` | `flamingo-next-production` |
| DB | `fns_staging` cluster/user | `fns_production` separate cluster/user |
| Object storage | `fns-stage-private` | `fns-prod-private` |
| Domains | `studio-staging.new-domain.example` | `studio.new-domain.example` |
| OAuth app | Dedicated test app | Dedicated production app |
| Secrets | `FNS_STAGE_*` | `FNS_PROD_*` |
| Queue namespace | `fns-stg` | `fns-prd` |

**Never alias either to `manhwa.nodepilot.dev` or the old Railway endpoint.** Provider IDs and origins must be recorded in the new project's environment inventory after the owner creates resources. All old resources are out of scope.

## 1. Provisioning order and mandatory checks

1. Owner approves a monthly infrastructure budget and new resources. Create a **new** private GitHub repo. Configure branch protection, mandatory CI, secret scanning and minimal access.
2. Provision independent staging Postgres and R2 buckets, no real publishing credentials. Enable encryption, backup retention and least-privilege service accounts.
3. Provision staging API, scheduler, research worker, AI worker, media worker and web as distinct services from **new Git remote**. Verify service source repo/branch. Disable automatic public publishing/Drive sync in all staging instances.
4. Configure staging auth with fresh keys. Block all untrusted domains except permitted provider APIs; no access to prior project IDs/domains.
5. Apply Alembic schema. Execute synthetic fixtures and database+object restore rehearsal before real chapter work.
6. Connect licensed/approved source adapters; set quota/spend policies and restrict number of paid requests. Run golden private episode.
7. Only when accepted, provision new production DB/bucket/API/worker/web with separate credentials; deploy image matching reviewed staging SHA and migration.
8. Publishing stays off, credentials absent until owner separately approves intended account, rights, exact export/package and limited first upload.

## 2. Deployment integrity

CD pipeline rules:

- Feature branch PR: Python/TS lint, typecheck, unit tests, JSON Schema/OpenAPI validation, migration smoke test, fake provider E2E, security/secret scan, synthetic MP4, no public API, no deploy to production.
- Staging: only approved new repo branch, deploy backend+frontend to staging, verify new service IDs, media storage, auth and job health; execute browser test and synthetic media.
- Production: manual owner environment approval after jobs idle/drain policy, verified release SHA, database backup snapshot, compatibility migration test and rollback plan. No force push; no automatic production deployment from mere documentation changes unless explicitly allowed by new repo policy.
- Deployment evidence: Git SHA, image digest, migration revision, DB cluster ID hash, storage bucket ID hash, feature flags, actual URL, health/readiness and smoke-test results. Never output secret values.

## 3. Environment variables (names and safe defaults)

| Key | Type / default | Rule |
|---|---|---|
| `ENVIRONMENT` | `local|staging|production` | Deny cross-environment connections |
| `DATABASE_URL` | secret, none | Different **new** DB per environment |
| `OBJECTSTORE_ENDPOINT` | URL | New private S3/R2 endpoint |
| `OBJECTSTORE_BUCKET` | string | New private bucket |
| `OBJECTSTORE_ACCESS_KEY`, `...SECRET_KEY` | secrets | No browser exposure |
| `SESSION_SIGNING_KEY`, `CSRF_SIGNING_KEY` | secret | Different stage/prod; rotation plan |
| `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` | configured | Dedicated new app registration |
| `PUBLISHING_ENABLED` | `false` | Independent hard server gate |
| `DRIVE_AUTO_COPY_ENABLED` | `false` | Do not couple to render |
| `AUTOPILOT_MODE` | `OFF` | Enrollment only after approval |
| `ALLOW_PROTECTED_SOURCE_SCRAPING` | `false` always | Do not enable unauthorized scraping |
| `ALLOWED_SOURCE_PROVIDERS` | blank | Only permitted/approved |
| `MAX_EPISODE_AI_USD` | example `10.0` | Configurable cap, not cost forecast |
| `MAX_DAY_AI_USD` | example `35.0` | Hard budget |
| `MAX_MONTH_AI_USD` | example `300.0` | Hard budget |
| `MAX_MEDIA_WORKERS` | example `1` | Process budget |
| `MAX_AI_WORKERS` | example `2` | Provider concurrency |
| `API_AUDIENCE`, `WEB_ORIGIN` | dedicated domains | Block old project origins |
| `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` | absent by default | Only new owner-approved OAuth app |
| `YOUTUBE_EXPECTED_CHANNEL_ID` | absent | Publishing impossible without verified value |
| `GEMINI_API_KEY`, `TTS_PROVIDER_KEY`, `VIDIQ_*` | absent | New access only, no implicit old secrets |
| `MEDIA_SIGNED_URL_TTL_SECONDS` | `300` | Short expiry |
| `LOG_LEVEL` | `INFO` | Never log secrets/prompts by default |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | optional new collector | Remove sensitive attributes |

**Never store these actual values in the repo.** GitHub Actions deployment should use OIDC/short-lived identity where supported; otherwise encrypted provider secrets with least scope.

## 4. Live operations and feature flags

Read-only status: worker count/leases, jobs in `queued/leased/running/paused`, AI budget, source rights, publishing flags, last backups, provider connections, queue, export/QA freshness, remote reconciliation. A deployment that restarts workers must safely drain running media stages or wait until idle. `cancel_requested=true` stays persisted across restarts. The scheduler cannot turn `PUBLISHING_ENABLED` on. Only owner-authenticated setting change can enroll series in produce mode.

**Emergency stop:** set publishing flag false, autopilot OFF, stop enqueue of new paid jobs, allow safe media worker checkpoint, revoke/disable external publishing credentials if incident warrants, preserve audit/events/backups; never delete queued records as a substitute for safe pause. After recovery reconcile remote upload sessions before resume.

## 5. Monitoring/SLO and alerts

Suggested objectives after launch, to be calibrated: warm p95 read <400ms at specified load, Home ready <2s, successful background lease recovery on restart, 100% authorized media access, no unauthorized publication, no critical corrupted published export. Alert on >3 repeated media failures/episode, unexpected usage increase, unverified upload, high queue age, license expiration, missing backups, persistent version mismatches or wrong account. Log request/trace/correlation IDs and exact artifact hashes, not media/secret bodies.

## 6. Backup and restore

**Backup plan:** PostgreSQL point-in-time recovery where supported, nightly logical dumps, bucket versioning/replication as available, manifest checksum snapshots, separate encrypted storage credentials; protect publication ledger and source rights manifests. Target RPO <=15m, RTO <=4h (objectives requiring plan verification, not guarantees). Retention aligned with creator/rights and provider rules.

**Monthly/quarterly recovery exercise** (as appropriate):

1. Record latest DB backup time and storage object inventory digest.
2. Create **new disposable recovery environment** with fresh credentials, zero outbound publishing/network permissions.
3. Restore DB then object snapshot; verify FK/integrity and object hashes; count series, episodes, source revisions, ledger entries, approval/report hashes.
4. Verify the latest source-to-final export and exact QA report are accessible in read-only mode.
5. Inspect running/leased jobs: no accidental resume or retransmission; confirm saved cancellations.
6. Smoke test UI under recovery domain with authorization.
7. Record elapsed recovery, missing artifacts, RPO gap, repair instructions. Destroy disposable resources after approval; never test restore by overwriting production.

## 7. Post-deployment smoke-test checklist

- `/healthz`, `/readyz`, frontend expected commit and API expected commit match the reviewed release.
- Anonymous access to artwork, storyboard, manifests, source OCR, reports and API docs is denied; session read works.
- DB source pages, canonical identities, work/episode counts, QA report and approvals match pre-release comparison.
- Create a new **QA-only** synthetic test production; does not touch real user queue.
- Export a local synthetic MP4; full decode and exact manifest pass; cost provider fakes used.
- Check `PUBLISHING_ENABLED=false` unless owner separately authorized a new release; no YouTube/Drive copy.
- Run autopilot dedup preview on a completed and archived episode; both skipped.
- Verify metadata field owner locks survive background preparation.
- Check backup timestamp, job/process health, alerts, request tracing, object-store signed URL expiry and memory/CPU.

## 8. Incident classes and playbooks

**Security exposure:** disable affected endpoint and secret, isolate app, audit access logs, rotate credentials, notify owner, inspect media permissions and provider requirements, preserve forensics.

**Unauthorized public action / duplicate upload:** set publish OFF, stop uploads, capture remote IDs and API attempts; reconcile before any retry; owner decides whether to private/delete remote content after considering provider controls. Do not silently change remote visibility.

**Stale owner metadata:** stop posting queue; show owner field provenance; restore previous owner revision as a proposal, verify automated prep idempotence, release only after isolated test.

**Broken source/canon:** freeze affected productions, compare source/alias revisions, invalidate only descendants, preserve previous approved outputs and require editorial review.

**Runaway cost:** disable new model reservations, compare API/provider actual usage, retain incomplete job state and verified outputs, seek owner budget decision.

**Worker zombie/resource exhaustion:** stop new render lease claims; graceful shutdown/kill controlled process group, verify PID1 reaping, preserve stderr and output manifests, recover only failed clips.

**Broken production release:** compare currently deployed image SHA and DB migration; rollback compatible application image or use tested restorative procedure; **never** wipe DB/volumes to clear status. Prove content ledger and approvals remain unchanged.

## 9. Infrastructure change-control policy

No automation may create paid cloud resources, alter OAuth scopes, move domains, change published video visibility, connect to the existing app, increase budgets, or enable publication without distinct recorded owner authorization. A new isolated project may be instantiated after approval; this runbook is not that approval.
