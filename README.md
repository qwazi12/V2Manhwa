# Flamingo Next Studio / V2Manhwa

An independent local workspace for authorized manhwa production: import pages, edit source-linked narration/shots, render a private narrated video, record QA findings, prepare packaging, and review the exact export.

## Run

Start Docker Desktop, then run:

```bash
./start-studio-docker.command
```

Open **http://127.0.0.1:3000** and enter the local key printed in the terminal. Python 3 and Docker Desktop are required on the host; Node/Python/media tools run in dedicated containers. First build downloads public dependencies and builds the pinned MinIO release. Keys are generated into ignored mode-0600 `.env.local`; no browser-bundled secret.

Optional local neural voices:

```bash
./download-voice-models.command --docker
```

This downloads two checksum-pinned public Kokoro assets and installs them in the project's private Docker volume. Inference is offline. Default system speech works without these model files. See [voice attribution](docs/VOICE_ATTRIBUTION.md).

`./start-studio.command` is the host-development alternative, requiring Python/Node and local FFmpeg, Tesseract and say/espeak-ng. `./start-codex.command` remains the original engineering handoff launcher; it starts a Codex CLI session.

**Current incident:** image builds pass but Docker Engine is timing out on container starts. Project volumes are preserved; the owner has been asked to restart Docker Desktop. The app is currently down. Startup is bounded and reports this failure; it does not restart shared Docker automatically.

## Local workflow

1. Create a series and import your authorized ordered PNG/JPEG/static WebP pages with an explicit rights declaration.
2. Review original/normalized source and optional local OCR. OCR and gutter suggestions remain unreviewed evidence.
3. Write and save source-linked beats, crops, motions and voice; every story page needs coverage. Review the source before approving the saved script.
4. Queue a longform render. The worker produces MP4, narration WAV, WebVTT and a source/frame/hash manifest. Jobs support cancel/retry; edits invalidate stale exports/approvals.
5. Inspect the actual video. Record timestamped story/voice/visual findings; P0/P1 findings block approval until an explicit retest.
6. Prepare episode-specific packaging and review the exact export privately. Vertical exports have separate plans/reviews and a 60-second cap.

The local owner session is development-only. Full automatic writer/independent critic/ASR, live research, watchlist, production identity, cloud staging, OAuth/publishing, Drive and autopilot remain unfinished or disabled. Nothing uploads publicly. Full status: [implementation evidence](docs/IMPLEMENTATION_STATUS.md), [ticket ledger](docs/ISSUE_LEDGER.md), [runbook](ops/PHASE0_LOCAL_RUNBOOK.md).

## Verify

With dedicated dependencies running:

```bash
./scripts/prepare_test_db.sh
make test check-contracts test-media
npm --prefix web run build
```

The complete suite last passed 32 tests before the latest image/OCR/pronunciation fixes. An 18-test offline subset and latest frontend build have since passed; a combined full rerun is pending Engine recovery. The separate synthetic media smoke is not full episode acceptance. No blueprint ticket is declared complete solely because tests pass.

Ports bind only to loopback: web 3000, API 8000, PostgreSQL 56473, private object store 59473, store console 59474. Dedicated Compose project: `v2manhwa-local`. Never substitute another application's resources.

`contracts/openapi.yaml` remains the future design; `contracts/local.openapi.json` is the implemented API. The target repository was public when inspected, so the specification's private-repository gate remains open. No cloud/deployment/visibility change is implied.
