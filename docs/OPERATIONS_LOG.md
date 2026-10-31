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

## 2026-10-31 — Expanded local build and runtime incident

- Implemented source ingestion, full schema migrations, source-linked editing, rights revisions, manual canon, OCR, render workers, offline speech/video exports, packaging, exact private reviews, QA findings and backup/restore. Current code remains local on feature/phase0-local-studio; the earlier public draft PR still represents the foundation.
- Full Python suite passed 32 tests before the latest WebP/TSV/pronunciation changes; separate fns_test and test bucket used. The latest 19-test offline subset passed. Latest Next production build, static contracts, synthetic media decode, Python compilation and shell syntax passed. Full rerun is pending infrastructure recovery.
- Browser exercised a saved/approved original Beacon sample, three shot motions, real completed render and loaded MP4: 23.376302 seconds, 1280×720, captions present, readyState 4, no media error. This is engineering fixture acceptance, not the owner's creative review of the real chapter.
- Real signed DB+media snapshot and disposable restore passed: 15 objects; studio_episodes 1, snapshots 4, source_pages 3, media_assets 7, canon_claims 0, render_jobs 1; zero restored sessions. A tampered snapshot manifest was rejected before restore. Existing source volumes unchanged.
- Installed Tesseract with Homebrew; Homebrew also performed its automatic update and cleanup. Installed Kokoro and transitive packages only in the project venv/container. Two official public voice assets downloaded and pinned by size/SHA. Neural speech smoke produced 7.58 seconds of mono 24 kHz audio; no external inference call.
- Public-image build initially stalled in the Docker credential helper. A local anonymous client configuration resolved image builds. Later, Engine container starts hung at created/Pid 0, including a direct start request to the local Unix socket. Only this project's Compose stack was reset, without deleting volumes. Desktop restart requested from owner; not performed autonomously. Web/API are currently down. Latest image runtime and model-volume installer remain unverified.
- Public chapter reader opened normally. An initial direct script request returned 403 and was not retried. Exported the 70 images actually loaded in the public browser using pageAssets; no failures. Preserved originals (30,747,518 bytes) and normalized PNGs (196,308,730 bytes), page order and SHA manifests under ignored work/authorized/.
- Recorded user statement: “I have permission for processing and public distribution.” No rightsholder name or separate license document supplied. No publication action performed.
- Ran local English OCR on all 70 pages and visually inspected all contact sheets. Found a literal-quote TSV parsing defect; a failing regression reproduced it before fixing csv quoting. Prepared a 70-beat, 1,713-word original recap draft, with rights/provenance and owner-review-pending labels. Real-source app import is pending Engine recovery.
- No vidIQ service calls, paid provider inference, OAuth, cloud provisioning, public upload, Drive copy, production deployment or old-project access.

- The first real chapter render exposed excessive video bitrate before final export. Interrupted that local draft, retained verified narration cache, and added a 1 Mbit/s VBV bound plus a new clip-cache version. A new bounded render is in progress; full suite remains pending. Frontend import limit corrected to 80 pages / 32 MB raw so the authorized chapter fits below the 45 MB request cap.

- Pushed code-only commit 81b89e2 to the existing feature branch after checking the new target remote and scanning staged files for generated local keys/runtime media. GitHub connector denied PR metadata update (403); browser successfully updated title/body while preserving draft status. Fresh hosted CI started. No merge/deploy.
- First authorized chapter MP4 passed technical QA: 711.542 seconds, 17,077 frames, 70 beats, 87,642,278 bytes. Frame inspection revealed empty-gutter scrolls, so it was rejected visually. Prepared focused illustrated crops, visually reviewed all 70 crop proposals, added subdued source-derived panel backdrops and slow zooms, and started a replacement private draft using all cached narration. Six offline actual filter/decode tests passed for the new backdrop/motion paths.

- Replacement authorized private draft finished: 711.542 seconds, 17,077 frames, 70 beats, 36,206,305 bytes, 1280×720, 70 voice-cache hits. Full decode/duration/frame/per-beat audible PCM QA passed. Inspected six actual final frames; focused panel shots replaced empty gutters. Separate local review viewer loaded readyState 4, one caption track, no media error; playback advanced to 40.342 seconds and was paused. Mobile 390×844 had no horizontal overflow. This viewer is not the main studio app, and this is not a full human listening/creative approval. Output files are outside Git.

- Final pronunciation review added rejection of blank character aliases and preserved Unicode dotted-I matches when casefold differs, avoiding accidental zero-length substitutions or worker exceptions. Latest 19-test offline subset passed.
