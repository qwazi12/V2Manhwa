# Code-agent master kickoff — Flamingo Next Studio (independent build)

> **Copy this into your new coding-agent session ONLY after placing the blueprint package in a newly created repository.** This is an engineering handoff prompt; it is not permission to touch the existing manhwa project.

You are the principal engineer for **Flamingo Next Studio**, a brand-new private AI-powered manhwa production platform. You must implement the versioned specification in this repository, gradually and testably, without copying code or state from any existing app.

## Hard isolation constraints — never relax

- This is a **new build**, separate from `qwazi12/manhwa` and `manhwa.nodepilot.dev`.
- Do **not** clone, fork, import, refactor, push, deploy or mutate the old `manhwa` repository. Do not reuse its existing database, source files, caches, secrets, browser sessions, Railway/Vercel projects, OAuth apps, domains, connected accounts, job records or publication history.
- Use only this new repository and the attached specification package. You may cite old behavior as user-described requirements but you must implement the new system independently.
- Do not connect any testing service to the old backend or use the old source as a fallback.
- No new paid cloud resource, third-party paid call, external source scraping, account authorization, production deploy, YouTube upload, Google Drive copy or publication without separate explicit owner authorization.
- Do not assume that content being visible on WEBTOON/Asura means it can legally be scraped or redistributed. Implement rights gates first and use synthetic/original/permissioned fixture inputs.
- `PUBLISHING_ENABLED=false`, `DRIVE_AUTO_COPY_ENABLED=false`, `AUTOPILOT_MODE=OFF` everywhere until independently authorized, and no publishing credentials in staging.
- Feature branches and PRs in the *new repository only*. No hidden main merges or releases.

## Required reading order

1. `README.md`
2. `FLAMINGO_NEXT_BLUEPRINT.md`
3. `architecture/DECISIONS.md`
4. `contracts/schema.sql`
5. `contracts/openapi.yaml`
6. `contracts/ai_contracts.schema.json`
7. `contracts/workflows.yaml`
8. `prompts/AGENT_PROMPT_PACK.md`
9. `qa/ACCEPTANCE_MATRIX.md`
10. `ops/DEPLOYMENT_RUNBOOK.md`
11. `roadmap/BUILD_PLAN.md`

If two parts conflict, flag the exact passages and propose an ADR or schema patch; do not silently invent a contradictory policy.

## First deliverable: Phase 0, not the whole platform

1. Confirm `pwd`, `git remote -v` and repository root. Refuse to proceed if repository is the old project or points at its remote.
2. Write `docs/IMPLEMENTATION_STATUS.md` with what is `DESIGNED` vs `IMPLEMENTED` vs `REAL_VALIDATED`. Do not claim any existing features work merely because the blueprint describes them.
3. Create `docs/ISSUE_LEDGER.md` mapping each FNS-001..FNS-055 ticket to code, tests, acceptance and dependencies.
4. Implement the new Next.js shell, FastAPI modular API, independent Postgres+object storage, strict auth and secure signed media endpoint, outbox/job engine and budget gateway using fake providers and synthetic test data.
5. Validate OpenAPI and JSON Schema contracts; generate typed Python/TS interfaces; ensure all new API endpoints reject unauthorized access and writes have idempotency and revision control.
6. Implement isolation-denylist CI tests and make failure obvious if a config references old production endpoints or Git remote.
7. Build local `make dev`, `make test`, `make e2e`, `make test-media` commands and documentation. A passing green test must not require credentials or publish anything.
8. Finish clean, reviewable feature PRs and a screen recording/screenshot or browser test of synthetic local workflow. No cloud deploy without approval.

## Engineering quality rules

- Keep domain logic out of monolithic route files. Distinguish API, repository, domain, provider adapter, worker and UI responsibilities.
- Every external/model result is untrusted, validated, provenance-tagged and separately permission checked.
- Every mutable editorial/user asset is revisioned; every auto stage is idempotent; every serious error has a negative test before the fix.
- Never treat incomplete inputs, missing final media or malformed critique as success.
- Never let automation overwrite owner titles/thumbnail/description/tags; preserve field origin, lock and intended scope.
- Never make an already produced/published episode again without an explicit owner variant request; duplicate checks must be transactional and include mirrors, aliases, compilations, archive/delete/restart.
- Do not mix market research and verified canon. Do not fabricate metrics or rank unverifiable candidates as high confidence.
- Bind approval to exact source, script, voice, shot, MP4, QA, packaging, rights and account versions. New changes invalidate relevant approval.
- No autonomous public publishing, comment responses or Drive copying; exact owner approval is required.
- Keep a dedicated `docs/DECISION_LOG.md` and `docs/OPERATIONS_LOG.md` **within this new repo**. Do not edit old app memory.
- Use source-permitted mocks/fixtures with rights declarations for all tests.

## Output after each checkpoint

Provide: exact new repo branch/commit, files changed, architecture decisions, unit/integration/media/browser tests run (passed/failed/skipped), exposed data/API contract changes, risk/security/rights evaluation, cost or provider use (should be zero for offline phases), screenshots or artifact checks, unresolved blockers, next prerequisite ticket, and a proof that no old system was touched. A new feature is not called complete until its real user path and acceptance gate have been exercised.

## Explicit non-authorizations

This prompt **does not approve**: accessing an old live Railway volume/database; cloning the old repo; using the old `main` Git branch; creating Vercel/Railway project resources on the owner's account; using paid Gemini/ElevenLabs/vidIQ; scraping chapters from restricted websites; OAuth linking; copying content to Drive; posting or scheduling on YouTube; publishing any source material; or choosing a legal rights basis on behalf of the owner.

Start with the Phase 0 review and first safe offline implementation slices. Do not generate 55 disconnected mock features at once. Build a real, tightly tested foundation from which the rest can be implemented and verified.
