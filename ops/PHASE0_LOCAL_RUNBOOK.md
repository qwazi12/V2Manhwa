# Local studio runbook

## Start / stop

Use `./start-studio-docker.command`. It initializes new local keys, builds dedicated images, starts the independent stack, migrates through 0003, initializes the private bucket and waits for application health. It refuses another process's web/API listener. Containers persist after the terminal closes.

```bash
bash scripts/docker_local.sh compose -f compose.yaml -f compose.app.yaml stop
```

Do not use `down -v` unless intentionally destroying this project's data. The project-scoped Docker wrapper uses a local Unix socket and anonymous config for public image pulls; it never modifies global Docker credentials/configuration. If container startup times out after 120 seconds, restart Docker Desktop manually and rerun the launcher. Do not restart shared Desktop automatically.

`./start-studio.command` starts API/web/two workers on the host and supervises their PIDs. It needs pinned venv/npm dependencies, FFmpeg, Tesseract and say/espeak-ng. Ctrl+C stops its host processes. `start-codex.command` launches the engineering handoff, not the application.

Infrastructure is exclusively `v2manhwa-local`, fns_local on 56473, private MinIO on 59473/59474. Test DB fns_test and test bucket are separate. Settings reject nonlocal infrastructure. Generated `.env.local` is ignored and mode 0600. Never copy keys into screenshots, documentation, browser code or command output shared externally.

## Optional local neural narration

`./download-voice-models.command` downloads/verifies models for host development. Add `--docker` after the application images have built to copy only pinned assets into the dedicated voice_models volume. The setup helper has no network and verifies staged checksums before replacing files. API/worker mount that volume read-only. Rendering fails if files are absent/changed; it never makes a paid/network fallback. The Docker volume installer is prepared but not yet runtime-verified during the current Engine incident.

## Verify

1. `./scripts/prepare_test_db.sh`; `make test` runs database/storage/media/security/migration tests on isolated test resources.
2. `make check-contracts` checks the future reference design; runtime drift is checked by tests. Export implemented schema with `PYTHONPATH=api .venv/bin/python scripts/export_runtime_contract.py`, then `npm --prefix web run generate:api`.
3. `make test-media` separately renders/decodes an original one-second fixture. `npm --prefix web run build` checks production UI/types; avoid sharing its .next directory with a dev server.
4. Browser: sign in, create original Beacon sample, save crops/motions/voice, source review + script approval, queue render, observe terminal status, play MP4/captions, inspect export facts and QA. Review package; test separate vertical variant/review, findings/retest, rights revoke, Bible and historical restore. Only confirm watched/source-reviewed statements actually performed by the acting reviewer.
5. At 390×844 verify no horizontal overflow and usable source/editor controls. Sign out and verify revoked-session denial. Latest complete browser regression is pending Engine recovery; older local evidence covers real Beacon export playback.

## Backup and restore

Run `PYTHONPATH=api .venv/bin/python scripts/backup_local.py create` to snapshot, then `PYTHONPATH=api .venv/bin/python scripts/backup_local.py verify <snapshot-directory>` to verify and perform a disposable restore drill. It refuses endpoints outside this project's dedicated loopback resources, validates its Compose owner labels, signs metadata and checks every object hash. Backup directories are private; active sessions are excluded from restored DBs. Restore drills create fresh nonce-named DB/bucket, verify counts/hashes, then clean only those disposable resources. No cloud restore claim.

## Authorized private draft preparation

`scripts/render_private_draft.py --plan <work-plan.json> --output <private-output-dir>` uses the same media engine with an isolated filesystem object/cache store. It validates processing rights, page links and source hashes, writes no application state and refuses claimed owner approvals. It is a review-artifact utility, not an app/database fallback or end-to-end proof. Keep artwork/plans/exports outside Git. Generated media has technical QA only and must be reviewed before release.

## Boundaries

Local owner auth is not production OIDC/MFA/multi-role access. Do not tunnel/expose loopback development services. Mock budget units are not USD. Real writer/critic/ASR, cloud recovery, connected research/analytics, OAuth/upload, Drive and autopilot remain unimplemented or disabled. Technical decode/audibility PASS never substitutes for semantic accuracy, voice listening or owner creative acceptance.
