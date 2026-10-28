# New-project decisions (append only)

## 2026-10-28 — Independent foundation
- New standalone application `flamingo-next-studio`; no inherited repo/history/resources.
- Keep the provided specification intact; add `AGENTS.md` as Codex's project-level instruction entry.
- Fake, offline demonstration API only until FNS-001 to FNS-010 are implemented properly.
- Deliberately defer all remote GitHub creation, hosting and provider authorizations. None are implicitly approved.

## 2026-10-28 — Local slice in owner-selected V2Manhwa

- The user supplied qwazi12/V2Manhwa as the target. It was empty and public. This supersedes the package's proposed repository name, but does not satisfy its private-repo acceptance gate; no visibility change is inferred.
- Execute the engineering handoff directly in the current chat instead of recursively launching another Codex agent. Preserve start-codex.command and add start-studio.command for running the app.
- Use dedicated PostgreSQL tables prefixed local_ for this constrained synthetic milestone, with a frozen reversible Alembic migration. The full designed schema remains a future migration.
- MinIO public images failed at Docker Hub and Quay. Build upstream RELEASE.2025-10-15T17-29-55Z from source at commit 9e49d5e7a648 instead. Docker build evidence validates availability, not production security/support.
- Use loopback ports 56473/59473/59474 after collisions on initial dependency ports; avoid taking over any existing listener.
- Local owner sessions use an ignored generated access key; no browser bundle key or production identity claim. No cloud/deploy/provider integration is enabled.
- Implemented response models generate a separate local.openapi.json and TypeScript file; leave the 48-path future API contract explicitly marked design-only.
- Original geometric SVG preview proves private object storage; it does not claim narration, video production, semantic QA or owner approval.
