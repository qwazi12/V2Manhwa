# Flamingo Next Studio — Model, OCR, TTS and external provider strategy

**Version 1.0 (reviewed 2026-10-28).** This is a proposed new-app default stack, contingent on separate owner API credentials, current model availability, costs and source usage rights. It does NOT read, reuse or migrate existing `manhwa` provider keys, prompt caches or connected accounts. Vendor model endpoints can change; pin a verified API model ID in this new app's configuration and archive its evaluation results.

## Reference implementation defaults (explicit choices)

| Task | Primary proposed implementation | Evaluation fallback | Selection rule |
|---|---|---|---|
| Panel geometry | OpenCV/shape/layout heuristics plus manually correctable masks | Licensed specialized segmentation model | Exact source preservation and panel gold-set quality |
| Text OCR | Local OCR using an appropriately licensed multilingual implementation; benchmark PaddleOCR language support first | Gemini multimodal extraction on ambiguous bubbles within budget | Text/reading-order precision on relevant Korean/English comic fixtures |
| Visual scenes | Gemini `gemini-3.8-flash` multimodal adapter *if available* | Separate approved multimodal model | Evidence-linked panel/event recall, hallucination rate, cost |
| Story map/script | Gemini `gemini-3.8-flash` as initial reference only | Escalated stronger model (`gemini-4-argon` only if access/cost authorized) | Human-reviewed story faithfulness and style |
| Independent critique | Separate prompt/version and context allocation; compare model output with gold annotations | Alternate approved model/provider if failure patterns correlate | Critical error recall; malformed outputs never PASS |
| TTS | ElevenLabs dedicated new API integration, **if separately authorized and license permits** | Gemini `gemini-3.8-flash-tts` evaluation on selected voices | Narrator consistency, pronunciation, emotional direction, cost, permitted commercial use |
| ASR/alignment | `faster-whisper` local ASR for transcript checks, plus VAD and forced alignment where appropriate | Authorized speech-to-text API | Accuracy for fictional names and timestamps; never claimed perfect |
| Renderer | FFmpeg + OpenCV and deterministic rational-frame timeline | Separate optional motion compositor (only for needed effects) | Full decode, synchronization, editability, reproducibility |
| Research | YouTube Data API + authorized publisher metadata + owner-entered catalogs | Explicitly approved vidIQ/Reddit/Trends adapter | Terms, scope, quota, data age and actual evidence |
| Thumbnail | Editor-controlled compositing of rights-cleared source art and original design layers | Approved image generation for original supplemental assets only | Truthful episode image, readability and rights |
| Publishing | New owner-authorized YouTube Data API OAuth app | Manual export/upload if app permissions unavailable | Strong channel identity and upload reconciliation |
| Analytics | Owner-authorized YouTube Analytics API | Owner-supplied authorized exports | Measured metrics with timeframe and source |

## Model-selection benchmark procedure

1. Prepare 12 licensed/synthetic gold episodes with annotated English/Korean OCR, speaker bubbles, events, canonical names, preferred narration, intentional pauses and image-matching labels.
2. Run at least two candidate configurations with equal evidence inputs, max tokens, prompt versions and temperature categories.
3. Record input/output token counts, run latency, actual provider spend, critical source-event recall, unsupported material claims, speaker accuracy, schema failure, edit time and reviewer rating.
4. Compare a quality-first and a cost-first configuration. Any model with unresolved critical source hallucinations or excessive omissions is disqualified regardless of price.
5. Choose a model **per stage**, not one model for everything. An expensive critique model only for low-confidence high-impact scenes may beat an all-episode expensive pipeline.
6. Require an explicit evaluation run before changing voice/model revision in a live series. Record all IDs and input fingerprints to invalidate only affected outputs.
7. Use bounded call budgets, never arbitrary unlimited automatic agent loops. Any unavailable provider returns `INCOMPLETE` and transparent alternative recommendations.

## Provider policy checklists

**YouTube:** API project quotas and OAuth scopes, intended channel ID, unverified upload behaviors, default privacy explicitly set, remote reconciliation; Analytics metrics only with first-party authorization.

**Gemini:** current model endpoint and modality support, input output pricing, tokens/image/file limitations, caching, content retention/terms and rights to send uploaded artwork to processor. No generation on copyrighted source content absent appropriate authorization.

**ElevenLabs:** voice license and commercial-use rights, character/usage pricing, streaming/retry behavior, consent for clones, known vendor voice ID, privacy and exact output audio format.

**Reddit:** separate commercial Data API agreement if required, deletion rules, prohibition on treating user content as unrestricted training material. Any inaccessible integration remains OFF.

**WEBTOON/Asura:** no assumption of authorized commercial source scraping or redistribution. Prefer owner-uploaded rights-cleared files and properly permitted metadata catalogs. Publisher source appearance doesn't prove either YouTube demand or permission.

**vidIQ:** a connected ChatGPT vidIQ tool is **not evidence of a separately licensed standalone service API**. Obtain specific developer product access and call budget from vidIQ before using a standalone adapter. Otherwise research continues with public YouTube Data API and permitted data.

## Cost governance

No up-to-date fixed dollar-per-chapter forecast is promised. Maintain provider-price schedules with `effective_at`, currency, unit, token/audio conversion, call quotas and account entitlements; compute and reserve before any job. Label $10/episode and $35/day as initial **configurable safety limits**, not projected bills. Capture actual provider billing reports for reconciliation and upgrade/revise limits only with owner approval.

## Sources verified 2026-10-28

- Google Gemini model catalog: https://ai.google.dev/gemini-api/docs/models
- faster-whisper reference implementation/license: https://github.com/SYSTRAN/faster-whisper
- YouTube API quota model: https://developers.google.com/youtube/data/determine_quota_cost
- YouTube Analytics: https://developers.google.com/youtube/analytics/dimensions
- Reddit API terms: https://redditinc.com/policies/data-api-terms
- WEBTOON Terms: https://www.webtoons.com/en/terms/
