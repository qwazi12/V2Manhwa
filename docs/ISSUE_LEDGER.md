# Ticket ledger — Flamingo Next Studio

No blueprint ticket is claimed complete. The limited starter supplies scaffolding only; complete status requires the exit condition in `roadmap/BUILD_PLAN.md`.

| Ticket | Deliverable | Status |
|---|---|---|
| FNS-001 | Create brand-new private repo, docs, ADRs, independent CI | DESIGNED (starter scaffold exists) |
| FNS-002 | Next.js app scaffold, design system, mobile tabs | DESIGNED (starter scaffold exists) |
| FNS-003 | FastAPI domain module scaffold, OpenAPI/Pydantic generation | DESIGNED (starter scaffold exists) |
| FNS-004 | Local Docker Compose: Postgres, MinIO, API, web, workers | DESIGNED (starter scaffold exists) |
| FNS-005 | New dedicated auth + role policy, CSRF and secure cookies | DESIGNED |
| FNS-006 | New PostgreSQL schema/Alembic, audit log and outbox | DESIGNED |
| FNS-007 | Private content-addressed storage, signed URLs and antivirus/archive safety | DESIGNED |
| FNS-008 | Durable jobs, leases, cancellations, idempotent outbox, fake costs | DESIGNED |
| FNS-009 | Budget reservation, model gateway and fake response fixtures | DESIGNED |
| FNS-010 | New staging environment + isolated restore and cost review | DESIGNED |
| FNS-011 | Work/edition/chapter identity with Unicode NFKC alias review | DESIGNED |
| FNS-012 | Rights manifest, per-action scopes and release gate | DESIGNED |
| FNS-013 | Upload authorized source bundle + immutable source revision | DESIGNED |
| FNS-014 | Panel extraction/geometry/reading-order classifier | DESIGNED |
| FNS-015 | OCR bubble/text preservation, speaker evidence basis | DESIGNED |
| FNS-016 | Series Room UI, names/pronunciation, canon proposals | DESIGNED |
| FNS-017 | Evidence references and source→panel→OCR linking | DESIGNED |
| FNS-018 | Scene/event assembler, coverage map and uncertainties | DESIGNED |
| FNS-019 | Scene/story outline, previous-episode continuity | DESIGNED |
| FNS-020 | Original script writer, beat provenance and style presets | DESIGNED |
| FNS-021 | Independent critic, targeted revision loop and incomplete states | DESIGNED |
| FNS-022 | Synchronized Source–Story–Video editing shell | DESIGNED |
| FNS-023 | Voice identity, pronunciation and licensed TTS adapter | DESIGNED |
| FNS-024 | Decoded speech QA, VAD/ASR alignment, silence analysis | DESIGNED |
| FNS-025 | Rational-frame timeline/shot planner with story anchors | DESIGNED |
| FNS-026 | Interactive shot preview, crop/turn/scroll editor | DESIGNED |
| FNS-027 | FFmpeg primary renderer, audio stem/master, atomic exports | DESIGNED |
| FNS-028 | Targeted rerender, asset graph/selective cache invalidation | DESIGNED |
| FNS-029 | Unified Q0–Q7 check contract and exact hash-bound reports | DESIGNED |
| FNS-030 | Final decoded MP4 QA, timestamps, technical/creative separation | DESIGNED |
| FNS-031 | Gold episode labeling/reviewer rubrics/repair UI | DESIGNED |
| FNS-032 | Approval fingerprints, invalidation and append-only audit | DESIGNED |
| FNS-033 | Stage reliability dashboard and failure recovery | DESIGNED |
| FNS-034 | Episode truth card, 3 title + 3 thumbnail concepts, source-supported description/tags | DESIGNED |
| FNS-035 | Owner field locks and correct episode/compilation inheritance | DESIGNED |
| FNS-036 | Rights-cleared thumbnail editor, mobile preview, versioned asset | DESIGNED |
| FNS-037 | Permanent made/published ledger, canonical alias-aware dedup | DESIGNED |
| FNS-038 | Watchlist/new-chapter tracking in WATCH/PREPARE modes | DESIGNED |
| FNS-039 | Private publishing queue and account identity verification UI | DESIGNED |
| FNS-040 | New Google Cloud OAuth app and YouTube integration, provider quota ledger | DESIGNED |
| FNS-041 | Resumable upload intent, remote reconciling, privacy explicit | DESIGNED |
| FNS-042 | Exact owner release/rights approval and emergency publishing stop | DESIGNED |
| FNS-043 | Staging failover, backup/restore and shadow publish dry runs | DESIGNED |
| FNS-044 | Research observation/evidence storage and search UI | DESIGNED |
| FNS-045 | YouTube official API public competitor adapter + time samples | DESIGNED |
| FNS-046 | Permitted catalog metadata/approved manual imports | DESIGNED |
| FNS-047 | Demand/supply scoring, red-team, confidence and rights gates | DESIGNED |
| FNS-048 | Optional vidIQ/Reddit/Trends adapters with permission ledger | DESIGNED |
| FNS-049 | Portfolio programming and consent-based new-pilot queue | DESIGNED |
| FNS-050 | Separate licensed vertical shot plans and Short QA | DESIGNED |
| FNS-051 | Community drafts/polls/comment themes, no auto posting | DESIGNED |
| FNS-052 | First-party YouTube Analytics/retention mapping | DESIGNED |
| FNS-053 | Packaging experiment tracker and observed outcomes | DESIGNED |
| FNS-054 | Audience-informed programming and creative feedback proposals | DESIGNED |
| FNS-055 | Reliability/creative dashboard tracking per-episode errors and human hours | DESIGNED |

## Local implementation evidence (2026-10-28)

All ticket completion/owner-acceptance gates remain pending. The following dependencies now have tested local implementation:

| Ticket | Code / acceptance evidence | Remaining dependency |
|---|---|---|
| FNS-001 | New V2Manhwa remote, fresh history, .github/workflows/ci.yml, tests/test_isolation.py (ISO-001/002) | Target is public; private setting and hosted CI proof |
| FNS-002 | web/app/page.tsx, globals.css; desktop/mobile browser workflow | Staging and owner acceptance |
| FNS-003 | API modules, models.py, local.openapi.json, generated-api.ts; tests/test_demo_api.py | Full product domains/contract implementation |
| FNS-004 | compose.yaml + scripts/run_local.sh/start-studio.command | Containerize app processes; clean-machine/staging verification |
| FNS-005 | security.py, local_sessions; ISO-007/008/012 subset | OIDC/MFA, HTTPS and invited role policy |
| FNS-006 | database.py, migrations/0001, test_migrations.py | Full product schema, actor audit and generic outbox consumers |
| FNS-007 | storage.py + original synthetic SVG; ISO-005/006 | Upload/archives/antivirus, full media type support |
| FNS-008 | repository.py/worker.py, concurrency/cancel/recovery tests; UI-007/009 local subset | Long jobs/heartbeats, generic event receipts, staging fault drills |
| FNS-009 | gateway.py strict FakeResult, transactional reservations/budget tests | Real-provider policy/accounting with separate authorization |
| FNS-010 | No cloud resources created | Approved independent staging, restore/cost/identity verification |

FNS-011–055 retain their designed-only status above. The private SVG is not FNS-027 episode video or FNS-030 final-MP4 QA.
