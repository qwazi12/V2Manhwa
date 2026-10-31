# Flamingo Next Studio — Architecture Decision Records (ADRs)

**Version:** 1.0, 2026-10-28. Decisions are defaults for the **new independent application**, not instructions to change the old app. A change requires a new ADR with trade-offs, migration consequences and tests.

| ADR | Decision | Rejected/deferred alternative | Reason / resulting trade-off |
|---|---|---|---|
| 001 | Create a brand-new private `flamingo-next-studio` repository; all-new cloud projects, storage, credentials, identity and CD | Fork/clone/deploy the existing `manhwa` repo | Must be independent; no silent shared backend, files or production jobs. Costs extra setup. |
| 002 | Single-user-first, optionally invited editors | Public SaaS/multi-tenant architecture | Removes billing/tenant complexity; still enforce auth and audit. |
| 003 | Modular Python monolith with separate worker processes | One enormous FastAPI file or microservice-per-agent | Bounded module contracts with simple operations, easier debugging. |
| 004 | Next.js TypeScript frontend | Desktop-only UI or Python-rendered admin pages | Responsive producer experience; added Node stack requires security maintenance. |
| 005 | PostgreSQL authoritative database | Scattered JSON/SQLite files as live truth | Transactions, unique constraints, concurrency and recoverability. More DB operations to own. |
| 006 | PostgreSQL job/outbox with leases and `SKIP LOCKED` initially | Cloud workflow SaaS or Redis/Temporal required on day one | Owner-scale cost/control; needs carefully implemented leases and idempotency; replace if complexity demands it. |
| 007 | S3-compatible private object storage, source SHA and immutable export objects | Single persistent local volume as media database | Independent workers and safer artifact hashes; object storage and transfer cost. |
| 008 | Canonical stable work/edition/episode IDs; alias collisions reviewed | Slugs as database keys | Avoid Unicode/title collisions and accidental shared series canon. |
| 009 | One Series Bible + versioned Episode Intelligence spine | Parallel memory stores per AI agent | Prevent split-brain identity; requires explicit schema evolution. |
| 010 | Model gateway with strict typed outputs and evidence references | Agentic browser with unrestricted context/tooling | Better repeatability and validation; more integration work. |
| 011 | Immutable artifact revisions and selective DAG invalidation | “File exists” cache or rerun whole chapter | Preserves owner edits and reduces cost; requires dependency tracking. |
| 012 | Frame-indexed timeline, FFmpeg primary renderer and full final-MP4 decode | Single prompt-to-video black box | Exact inspection and repair; heavier media engineering. |
| 013 | Separate deterministic technical QA, model semantic QA and human creative QA | AI self-rated 9/10 as release gate | Honest verdicts; higher editorial cost. |
| 014 | Publish disabled by default and owner approval bound to exact export, metadata, rights and channel | Fully autonomous end-to-end uploading | Prevent unsafe surprises; slower throughput. |
| 015 | Permanent canonical content/dedup ledger independent of folders and queues | Rely on watchlist or project folders to detect “made” | Robust duplicate prevention across mirrors/restores/compilations. |
| 016 | Research observations measured and dated with sample coverage | Lifetime views/age labeled current VPH or invented search volume | Reproducible opportunity decisions; slower collection and unknown values. |
| 017 | Dedicated Rights Manifest and licensed/approved input adapters | Unlimited downloading of aggregator art | Sources being accessible does not grant reposting rights; some series may be blocked. |
| 018 | Do not require vidIQ as a core dependency | Assume ChatGPT connector implies standalone vidIQ API entitlement | Provider functionality/terms must be independently authorized. |
| 019 | Compare title/thumbnail with observed owner analytics | Treat heuristic SEO score as performance forecast | Optimizes actual viewer behavior; data is lagged and observational. |
| 020 | Staging and production deploys are new isolated resources | Share production DB/storage for easier tests | Safe previews and recoveries; extra cost. |
| 021 | Rights unknown blocks public publishing; rights clearance is separate from technical green light | “I provided images” implies rights | Copyright and provider terms need independent basis. |
| 022 | Product does not auto-connect social networks, auto-reply or auto-share to Drive | Destination inferred from prior account preferences | Account and publishing mistakes are high impact. |
| 023 | Use creator-owned style kits and licensed assets; no copied competitor artwork or misleading thumbnails | Clone highest-performing thumbnails verbatim | Reduces rights and brand risks; requires creative design effort. |
| 024 | Instrument AI spend and human repair time | Optimize total generated minutes only | Editorial quality and net efficiency are the product outcomes. |
| 025 | Optional migration only after a future explicit import contract | Automatic import of existing project DB and caches | Protect current live project and prevent importing unverified/uncleared content. |

## Alternatives revisit triggers

**Queue engine:** At >10 concurrent long-running productions, persistent frequent lease/cancel bugs, or multi-region workers, evaluate a dedicated workflow orchestrator such as Temporal with a migration from current job/outbox state. Keep job IDs and artifact identities stable. Do not migrate for fashion.

**Media pipeline:** Evaluate Remotion/Chromium only for scenes whose rendering requirements exceed stable FFmpeg/OpenCV. Keep deterministic shot plan and exact source/clip manifests. Render subprocesses need PID1 init and bounded child-process cleanup.

**Vector search:** For >100k searchable events/claims, consider pgvector or a permitted embedding store, but lexical IDs and exact provenance always remain primary. Do not make embedding similarity a source-truth validator.

**Analytics:** Platform-native YouTube Studio experiment results are preferable when available; no undocumented API-based A/B test control is assumed. UI may let owner export test concepts and record outcomes manually.

**Privacy:** Private status does not exempt software from provider terms, copyright, auth security or data-retention rules. All cloud systems are nevertheless independent.
