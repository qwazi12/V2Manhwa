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

## 2026-10-31 — Local production workflow and explicit limits

- The user's instruction to continue the complete build extends beyond the original Phase 0 handoff checkpoint. Implement product slices locally while retaining the blueprint's independent-resource and release boundaries.
- Apply the full frozen product schema in migration 0002 and append studio snapshots/commands. Work UUID and edition/chapter identity remain authoritative; titles and aliases are not deduplication keys.
- Use PostgreSQL render leases/heartbeats and exact source/script/voice/canon/rights bindings. Technical FFmpeg decode/audio checks never imply semantic or creative approval.
- Choose offline system speech plus optional pinned Kokoro ONNX CPU voices; inference has no network download, account, credit usage or fallback. Ambiguous approved pronunciation aliases retain their original spoken spelling.
- Preserve exact PNG/JPEG/WebP originals separately from normalized render images. Reject animation, archives and URL input. Increase bounded decoded chapter allowance to 256 MB for the authorized 70-page chapter; raw request remains 45 MB.
- Add append-only human QA findings: P0/P1 block approval and persist through rerenders/variants until explicit retest. Rights/canon/script/package edits invalidate the appropriate approvals.
- Use project-scoped anonymous Docker configuration for public image builds because the credential helper stalled metadata lookup. Do not change global Docker configuration. Container starts subsequently failed at Engine level; request owner restart rather than restart a shared Desktop autonomously.
- User declined optional vidIQ analysis. No vidIQ service call/credits. Public YouTube playback was unavailable, so exact reference pacing/audio remains unverified.
- User attested permission for processing and public distribution of the supplied source. Preserve that statement without inventing the rightsholder name or license document. This authorizes media preparation, not an upload/release action.
- A standalone private-draft utility can use the same media engine while infrastructure is down. It writes no application state or owner approvals and is not an application fallback or end-to-end runtime proof.

## 2026-10-31 — Fresh-container verification during local Engine outage

- Use the existing new-repository CI runner to verify clean container startup and the complete Next proxy → authenticated API → dedicated PostgreSQL/MinIO → durable worker → private export path, while the owner Mac Engine is unavailable. Only original fixture media is used in CI.
- Keep this HTTP smoke separate from browser playback, source owner review and release approval. A passing hosted build does not imply the Mac runtime has recovered or the full 55-ticket platform is complete.
