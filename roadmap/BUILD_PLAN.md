# Flamingo Next Studio — Independent build program, dependencies and release gates

**Version:** 1.0. All implementation happens in a **new, clean repository**. The existing `qwazi12/manhwa` project is not the base or data source. No permission is given to change it, copy secret/config/media, or deploy it. A separate new product owner approval is needed for creating paid cloud resources and invoking nonfree external services. This file is the authoritative implementation sequence for the companion blueprint.

## Product launch philosophy

Build *vertical slices* that produce evidence, not departments built in isolation. A feature is `Complete` only when its UI path, persisted data, security, tests, staging execution and owner acceptance are demonstrated. `Designed`, `Mocked`, `Implemented`, `Integrated`, `Real-validated`, `Owner-accepted`, `Released` are distinct labels. The first meaningful success is **one rights-cleared, full script→voice→shot→MP4→QA→package private episode**, not a dashboard filled with synthetic cards.

## Prerequisite decisions to record in new repo

- Owner-selected new product/repo/domain name (use placeholders until decided).
- Approved new hosting/provider accounts, credentials and cost envelope; avoid defaulting to old connected accounts.
- First licensed or otherwise authorized chapter bundle for the gold test; specify allowed internal use and public release rights separately.
- Creator's narration tone and acceptable pronunciation/quality examples.
- Default language(s), target long-form format, aspect ratio and preferred first distribution platform.
- Legal review/rights sign-off on each source/work and intended distribution use.

Unresolved choices do not prevent offline core development with synthetic, original, or permissioned fixtures.

## Work-stream ownership

- **Platform lead:** architecture, schema, API, identity, isolation, auth, infrastructure, deployment.
- **Story intelligence engineer:** source panel/OCR, character resolution, evidence/event graphs, writer/critic.
- **Media engineer:** voice, alignment, shots, renderer, QoS, actual final-media QA.
- **Growth engineer:** researcher, opportunities, packaging, destination integrations, analytics.
- **Editor/product QA:** creator workflow, labels, real output review, source/event gold annotations, quality policy.

One engineer can sequentially do these; they are roles, not a mandate to hire.

## Phase 0 — independent platform, no real provider accounts

| Ticket | Deliverable | Depends on | Proof/exit condition |
|---|---|---|---|
| FNS-001 | Create brand-new private repo, docs, ADRs, independent CI | None | Remote is not old repo; no inherited history, secrets or media |
| FNS-002 | Next.js app scaffold, design system, mobile tabs | 001 | Homepage and accessible login shell work locally |
| FNS-003 | FastAPI domain module scaffold, OpenAPI/Pydantic generation | 001 | OpenAPI schema compiles to TS/Python types |
| FNS-004 | Local Docker Compose: Postgres, MinIO, API, web, workers | 002,003 | `make dev` with fake providers works from clean checkout |
| FNS-005 | New dedicated auth + role policy, CSRF and secure cookies | 002,003 | Anonymous media access and wrong-user role fail closed |
| FNS-006 | New PostgreSQL schema/Alembic, audit log and outbox | 003,004 | Fresh create + upgrade + downgrade tests; no old DB |
| FNS-007 | Private content-addressed storage, signed URLs and antivirus/archive safety | 004,006 | Checksums, expiry, path traversal and tamper tests |
| FNS-008 | Durable jobs, leases, cancellations, idempotent outbox, fake costs | 006 | Restart, race, cancel and retry tests |
| FNS-009 | Budget reservation, model gateway and fake response fixtures | 008 | No provider call without approved reservation; no real network in CI |
| FNS-010 | New staging environment + isolated restore and cost review | 001–009 | Verify unique IDs, denied old endpoints and restore drill |

**Phase 0 exit:** Owner can log in to separate staging, submit an entirely fake episode job, view a state transition and signed media preview. Zero external side effects, zero old-project interactions.

## Phase 1 — canonical identity, rights and source ingestion

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-011 | Work/edition/chapter identity with Unicode NFKC alias review | 006 | Identity collisions/novel adaptation tests pass |
| FNS-012 | Rights manifest, per-action scopes and release gate | 006,011 | Unknown/expired rights block public distribution |
| FNS-013 | Upload authorized source bundle + immutable source revision | 007,011,012 | Page/order/hash counts; zero source overwrite |
| FNS-014 | Panel extraction/geometry/reading-order classifier | 013 | Gold set coverage; decoration classified but source retained |
| FNS-015 | OCR bubble/text preservation, speaker evidence basis | 014,009 | Bubble-only and consecutive bubbles retained in order |
| FNS-016 | Series Room UI, names/pronunciation, canon proposals | 011,015 | Owner can approve alias/canon without changing raw source |

**Exit:** Independent rights-cleared chapter is searchable, inspectable and source-complete; canonical names preserve uncertainty and current source evidence.

## Phase 2 — Episode Intelligence and script reliability

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-017 | Evidence references and source→panel→OCR linking | 015 | Every displayed quote/claim links to immutable source |
| FNS-018 | Scene/event assembler, coverage map and uncertainties | 016,017 | Major gold events found/reviewed, no invented ID accepted |
| FNS-019 | Scene/story outline, previous-episode continuity | 018 | Source-supported causal outline |
| FNS-020 | Original script writer, beat provenance and style presets | 019 | Strict schema and anchored script with no assistant chatter |
| FNS-021 | Independent critic, targeted revision loop and incomplete states | 020 | Known omission/hallucination fixtures identified |
| FNS-022 | Synchronized Source–Story–Video editing shell | 018,020 | Clicking line jumps to panel and event; revision/undo |

**Exit:** Creator can inspect a chapter, see events and source links, and approve a genuinely reviewed script with zero unresolved critical story errors.

## Phase 3 — voice and media

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-023 | Voice identity, pronunciation and licensed TTS adapter | 020,009 | Same character pronounced consistently with rights/consent |
| FNS-024 | Decoded speech QA, VAD/ASR alignment, silence analysis | 023 | Silent MP3/corrupt voice caught even with music |
| FNS-025 | Rational-frame timeline/shot planner with story anchors | 018,024 | Expected audio/video spans and evidence-linked crop |
| FNS-026 | Interactive shot preview, crop/turn/scroll editor | 022,025 | Real shot preview; no blind tall-page rotation |
| FNS-027 | FFmpeg primary renderer, audio stem/master, atomic exports | 024–026 | Full private MP4 and complete source-to-shot manifest |
| FNS-028 | Targeted rerender, asset graph/selective cache invalidation | 027 | One spoken correction rerenders only affected dependent assets |

**Exit:** Owner can watch the correct finished *private* MP4, inspect exact scene timing, select/fix a shot, and replay approved audio with no missing narration or desync.

## Phase 4 — Quality Director, benchmark and release boundaries

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-029 | Unified Q0–Q7 check contract and exact hash-bound reports | 012,018,027 | Missing input != pass; critical defects block |
| FNS-030 | Final decoded MP4 QA, timestamps, technical/creative separation | 027,029 | Bad fixture found, sample frames/listening reviewed |
| FNS-031 | Gold episode labeling/reviewer rubrics/repair UI | 018,021,030 | Paired review with source and failure evidence |
| FNS-032 | Approval fingerprints, invalidation and append-only audit | 028–031 | Stale approval denied after asset edit |
| FNS-033 | Stage reliability dashboard and failure recovery | 008,029 | Restart/cancel/retry for failed midrender stage works |

**Exit:** One full source-to-script-to-render review completes with explicit reported technical and editorial limitations, a verified repair and immutable acceptance metadata. This is before public posting.

## Phase 5 — packaging, anti-remake autopilot and private queue

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-034 | Episode truth card, 3 title + 3 thumbnail concepts, source-supported description/tags | 018,029 | No invented chapter summary or CTR claims |
| FNS-035 | Owner field locks and correct episode/compilation inheritance | 034,032 | Periodic automation cannot reset owner title or copy chapter 32 to 34 |
| FNS-036 | Rights-cleared thumbnail editor, mobile preview, versioned asset | 034,007 | Correct scene, legible, separate aspect ratio variants |
| FNS-037 | Permanent made/published ledger, canonical alias-aware dedup | 011,006,032 | Past published chapters never automatically remake |
| FNS-038 | Watchlist/new-chapter tracking in WATCH/PREPARE modes | 037,012 | No unauthorized provider ingestion or paid generation |
| FNS-039 | Private publishing queue and account identity verification UI | 032,035,037 | Same video/metadata/channel approval set and no upload |

**Exit:** Finished episode has truthful packaging and verified dedup; owner can view queue safely. Publishing remains **OFF**.

## Phase 6 — first public release pathway

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-040 | New Google Cloud OAuth app and YouTube integration, provider quota ledger | 039 + owner account approval | Intended channel ID and scope match; current quotas documented |
| FNS-041 | Resumable upload intent, remote reconciling, privacy explicit | 040 | Uncertain remote result never double posts |
| FNS-042 | Exact owner release/rights approval and emergency publishing stop | 041 | No external effect when flag off, rights unknown or export stale |
| FNS-043 | Staging failover, backup/restore and shadow publish dry runs | 042 | All P0 tests pass before first approved public upload |

**Exit:** With separate explicit authorization, one approved video can be uploaded only to the verified connected owner channel and the result reconciled. Nothing is auto-public by default.

## Phase 7 — Research Investigator and external demand evidence

Build a *narrow researcher* early for programming, then expand with actual provider access.

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-044 | Research observation/evidence storage and search UI | 006,011 | Dated source URLs, sample coverage and missing data visible |
| FNS-045 | YouTube official API public competitor adapter + time samples | 044 + approved API project | Real measured deltas, no lifetime-average velocity confusion |
| FNS-046 | Permitted catalog metadata/approved manual imports | 044 + provider terms | Untracked new series, verified identity, no unauthorized chapter scraping |
| FNS-047 | Demand/supply scoring, red-team, confidence and rights gates | 045,046 | Saturated breakout A-tier downgraded when evidence warrants |
| FNS-048 | Optional vidIQ/Reddit/Trends adapters with permission ledger | 047 + separate access agreement | Provider can be disabled without breaking other research |
| FNS-049 | Portfolio programming and consent-based new-pilot queue | 047,037 | 15–30 candidate evidence report, pilot only on owner greenlight |

**Exit:** Researcher finds a genuinely new non-watchlist title, provides independent dated observations and a negative case; a missing provider stays explicitly unavailable. No false saturation estimates.

## Phase 8 — Social, analytics and quality learning

| Ticket | Deliverable | Depends on | Proof |
|---|---|---|---|
| FNS-050 | Separate licensed vertical shot plans and Short QA | 027,034 | Original vertical story with source/evidence and independent approvals |
| FNS-051 | Community drafts/polls/comment themes, no auto posting | 050 | No automatic public comment spam |
| FNS-052 | First-party YouTube Analytics/retention mapping | 041 + authorized channel | 100-bin retention position mapped to shot ranges with uncertainty |
| FNS-053 | Packaging experiment tracker and observed outcomes | 052,034 | Observed CTR/watch-time contextualized; no false causal claim |
| FNS-054 | Audience-informed programming and creative feedback proposals | 047,052,031 | Suggestions require human review and do not overwrite canon |
| FNS-055 | Reliability/creative dashboard tracking per-episode errors and human hours | 029,052 | Manual correction burden trending over multiple episodes |

**Exit:** Approved long-form releases generate separately approved social assets and permitted analytics feedback; no autonomous public interactions.

## PR strategy and review process

- Each ticket or small cohesive dependency group gets its own feature branch and PR in the **new** repo. Do not stack huge opaque PRs if independent diff can be reviewed.
- `feature -> review -> staging deploy -> synthetic/real QA -> owner approval -> main` for new project only.
- Maintain `docs/DECISION_LOG.md`, `docs/OPERATIONS_LOG.md`, and milestone state in this new repo. Do NOT write to any old project's `memory.md` or Git branches.
- Regression required for each bug. UI screenshots/test traces, fixture/actual media hashes, PR diff, cost and safety impact accompany code review.
- No production worker auto-deployment while jobs active without safe drain/lease behavior and verified backup; guard release with environment protection.

## Effort and staffing estimates

Effort sizes are relative engineering complexity, **not delivery promises**. Foundation/data/workflows: **L**; gold semantic annotation/quality and media: **XL**; initial source/packaging/research: **L**; reliable external publishing: **M–L**; long-term social/analytics: **L–XL**. Costs and actual elapsed schedule depend on lawful source availability, provider approvals, developer availability, workload, account tiers and quality acceptance. Avoid treating all 55 tickets as independent one-day tasks.

## What to measure at every release

- Technical: stage success, crash/retry rate, p95 API, render failure, storage/backup, GPU/CPU consumption, model cost, quota use.
- Editorial: source coverage, material unsupported claims, name disagreements, narrator defects, visual mismatches, median correction time, per-episode human approval score.
- Growth: impression/CTR/retention/subscription outcomes *after* publishing with comparable cohort windows; no unearned predictions.
- Safety: zero old-project touches, unauthorized spends/uploads, wrong-account actions, unapproved duplicates or missing rights gates.
