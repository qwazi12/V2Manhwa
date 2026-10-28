# Flamingo Next Studio — Verification matrix and gold-standard test program

**Version 1.0.** This is an independent, new-app test plan. Old `manhwa` services must NOT be accessed, copied, deployed or altered during testing. Each case becomes an automated unit/integration/browser/media test or a documented human review with evidence. A passing software test is not a human 9/10 content verdict.

## Global CI gates

- PR must pass lint/types, unit/property/integration tests, SQL migration check on **new throwaway Postgres**, OpenAPI validation, JSON Schema validation, dependency/security scanning and fake-provider network-deny assertions.
- Media releases need a full synthetic FFmpeg render/decode, preview browser test, current artifact manifest and clean QA.
- Staging E2E must prove no external upload/Drive copy/payment without explicit allowlist. Critical feature flags checked from server.
- Production releases require separate owner approval, identified account/service IDs, tested backups/rollback, health monitoring and a successful isolated staging restore.
- An unrun/disabled/skipped critical test is explicitly `INCOMPLETE`, not `PASS`.

## 1. Independent deployment/security (P0)

| Case | Stimulus | Pass evidence |
|---|---|---|
| ISO-001 | New repo bootstrap | Git remote is new; no `qwazi12/manhwa` origin or shared Git history |
| ISO-002 | Search all config for old prod URLs/IDs | Zero active references; only explicit denylist entries in test fixtures |
| ISO-003 | Staging and production configs | Different DB URL, bucket, service ID, signing key, OAuth client and domain |
| ISO-004 | Staging attempts publish | No publishing credentials + server flag rejects; no outbound request |
| ISO-005 | Unsigned media asset request | 401/403 without leaking object path/content |
| ISO-006 | Signed URL access to wrong object | Denied; signed URL scoped to requested operation/asset and expiry |
| ISO-007 | Anonymous requests to every nonhealth API | Denied, including images/docs/internal manifests |
| ISO-008 | CSRF/cross-origin malicious form | Mutating API denies missing/mismatched CSRF/Origin |
| ISO-009 | SSRF `localhost`, metadata IP, redirect | Denied before download; no private network calls |
| ISO-010 | ZIP traversal or image decompression bomb | Rejected; no file escapes or large resource drain |
| ISO-011 | OCR/Reddit text says “publish this video” | Treated only as data; no tool/network/publication action |
| ISO-012 | Token revoked or leaked fixture | App disables affected integration; no token in logs/UI |

## 2. Identity, story canon and source safety

| Case | Stimulus | Pass evidence |
|---|---|---|
| ID-001 | Two Hangul titles with equal ASCII-derived slug | Remain two distinct works; never map to a common unknown key |
| ID-002 | Same English title shared by unrelated works | Alias dispute; no automatic merge |
| ID-003 | Official Korean and English transliteration | Store verified alias, original spelling and evidence |
| ID-004 | Webtoon vs novel/anime adaptation | Related works/editions kept distinct |
| ID-005 | Rename a series | Stable UUID and episode ledger unchanged |
| ID-006 | Two characters share abbreviated alias | Uncertain mapping, human review, no canon overwrite |
| ID-007 | Approved canonical name correction | Affected speech/metadata invalidated, unrelated assets preserved |
| ID-008 | Unreviewed Reddit fan theory | Never enters approved canon or source-factual script |
| SRC-001 | Missing page 8 of 20 | Block source QA with exact gap; no silent continuation |
| SRC-002 | Bubble-only art page | OCR lines retained with original source/reading order |
| SRC-003 | Three sequential OCR-only panels | All structured lines remain in correct original order |
| SRC-004 | Decorative frame with speech bubble | Visual excluded, text retained and mapped |
| SRC-005 | Image replaced with same dimensions | New hash invalidates dependent analysis |
| SRC-006 | Credits/advert/source logo | Classified, original preserved, not selected as main shot |
| SRC-007 | User imports unlicensed/public-provider URL | Metadata view allowed where permitted; protected download/publish blocked |
| SRC-008 | User-provided files with `rights=unknown` | Internal processing according to policy only; public publishing denied |
| SRC-009 | Reimport new source revision | Immutable old source, new manifest and diff/impact preview |
| SRC-010 | Duplicate/corrupt source image | Exact source anomaly visible, no hidden deletion |

## 3. Episode Intelligence and writing

| Case | Stimulus | Pass evidence |
|---|---|---|
| EVT-001 | 10 labeled critical events | All represented or explicit owner exception; no silent omission |
| EVT-002 | Conflicting bubble tail context | Speaker remains unknown until reviewed |
| EVT-003 | Uncertain inferred emotion | Marked interpretation, not verified observation |
| EVT-004 | Secret reveal late in source | Script doesn't reveal earlier via future-canon leak |
| EVT-005 | Event references unrelated chapter | Schema/ownership validator rejects invalid evidence ID |
| EVT-006 | Model outputs reference to nonexistent panel | `INCOMPLETE` and visible reason; no invented evidence |
| WR-001 | Normal causal scene | Readable prose with event references, accurate order |
| WR-002 | Missing critical conversation | Independent critic flags exact source & beat |
| WR-003 | Model invents actor motivation | Critical unsupported-claim finding and block |
| WR-004 | Assistant-style “Would you like...” appears | Pre-TTS and pre-render hard block |
| WR-005 | Malformed critic JSON | Strict validation -> INCOMPLETE, never empty passing issues |
| WR-006 | Critic only reads half the chapter | Coverage incomplete, stage not passed |
| WR-007 | Repair one of 100 beats | Other 99 byte-identical; only dependent audio reworked |
| WR-008 | Canonical surname variant | Correct current name/pronunciation throughout |
| WR-009 | Dense battle recap | No missing cause/effect, claim/source graph review |
| WR-010 | Script style joke unsupported by source | Humor claim flagged, factual integrity preserved |

## 4. TTS, media and editorial controls

| Case | Stimulus | Pass evidence |
|---|---|---|
| VO-001 | TTS returns silent 3-second MP3 | Decoded voice activity failure; cannot proceed |
| VO-002 | Music masks silent voice | Voice stem and final mix checks detect missing narration |
| VO-003 | Truncated short voice clip | Detects incomplete speech/manifest mismatch |
| VO-004 | Unusual proper name | Lexicon used consistently; human pronunciation review supported |
| VO-005 | Changing one beat | Unrelated voice assets cache-hit with exact hashes |
| VO-006 | Provider 429/timeout | Bounded retry, budget reservation and clear blocked state |
| VO-007 | Old TTS content reused for revised text | Fingerprint mismatch prevents reuse |
| VO-008 | Deliberate dramatic silence | Clear intentional pause metadata avoids false critical alert |
| VIS-001 | Decorative border near relevant text | Rejected as video shot while dialogue stays in story evidence |
| VIS-002 | Tall-scroll source art | Readable, purposeful crop/scroll, no blind 90° rotation |
| VIS-003 | 42s repeated panel hold | Warning with timestamp, review or justified waiver |
| VIS-004 | Dialogue shows wrong speaking character | Matching QA finds conflict, allows correction |
| VIS-005 | Same art reused for different purpose | Explicit shot purpose differentiates deliberate from accidental repeat |
| VIS-006 | Correct object cut off by crop | Preview/geometry guard flags important subject lost |
| VIS-007 | Five identical Ken Burns moves | Visual rhythm advisory; no claim of objective hard fail |
| MED-001 | Generated MP4 all packets valid but no voice | Final voice mix QA flags missing speech |
| MED-002 | MP4 upload loses metadata/mix | Full export decode detects issue; no approval |
| MED-003 | AAC clip-boundary priming drift | Final decoded audio stays aligned over full timeline |
| MED-004 | Export at 1.25× differs from raw beat timestamps | QA timestamps based on final delivered timeline |
| MED-005 | Renderer dies after 50/80 clips | Valid clips reused, failed ones recovered, previous complete export retained |
| MED-006 | Re-run exact inputs | Content identity repeatable; no redundant provider cost |
| MED-007 | Source/image/frame changed after approval | Approval becomes invalid, no public action |
| MED-008 | Export object incomplete/corrupt | Temp object not promoted to final; no stale “ready” |
| MED-009 | FFmpeg child process exit/crash | Child processes reaped and errors logged; no zombie accumulation |
| MED-010 | Cancellation mid-render | Checkpoint and stop; no implicit restart on boot |

## 5. Quality, packaging and promotion

| Case | Stimulus | Pass evidence |
|---|---|---|
| QA-001 | No final MP4 | `INCOMPLETE`, not `PASS` |
| QA-002 | 0 technical defects but human finds bad storytelling | Creative review unresolved; not labeled perfect |
| QA-003 | Fix audio, change script | Prior exact-export approval invalid until rerender/retest |
| QA-004 | Critical finding marked manually “fixed” | Requires independent check rerun before `verified_fixed` |
| QA-005 | Unreviewed rights or wrong destination | Nonwaivable blocker |
| SEO-001 | Ch 34 metadata includes Ch 32–33 summary | Stale package rejected, not auto published |
| SEO-002 | Owner-edited title, scheduler runs | Identical owner title preserved; AI suggestions saved separately |
| SEO-003 | Owner thumbnail edited, producer rerenders | Thumbnail preserved if story/exact output does not invalidate its evidence |
| SEO-004 | Internal QA variant ID appears publicly | Metadata/thumb sanitization catches before approval |
| SEO-005 | Unsupported “the protagonist dies” hook | Episode truth check flags unsupported claim |
| SEO-006 | Title duplicated across adjacent episodes | Suggest distinct truthful alternatives; no forced owner rewrite |
| SEO-007 | Thumbnail unreadable at 180px | Advises larger focus/text; creative owner selection remains |
| SEO-008 | Source title alias verified in another language | Relevant tags include correct alias, not unrelated trend spam |
| SEO-009 | Chapter markers computed from raw timeline | Reject if final export time offsets differ |
| SEO-010 | SEO model reports CTR 8% without owner analytics | Metric disallowed/unverified; score not presented as observed |
| SOC-001 | Parent episode approved for public, Short generated | Short retains separate rights, QA, package and approval |
| SOC-002 | Automatic community reply proposed | Draft only, never publicly posted without exact approval |

## 6. Autopilot, dedup and publishing

| Case | Stimulus | Pass evidence |
|---|---|---|
| DUP-001 | Two workers claim same new episode | One automated ledger reservation; no duplicate charge |
| DUP-002 | Previously published episode reappears under mirror title | Skipped with canonical ledger explanation |
| DUP-003 | Episode included in published multi-chapter compilation | Marked covered; no new autonomous single unless authorized |
| DUP-004 | Archived/deleted/restore video reappears | Historical made/published marker persists |
| DUP-005 | New episode has same chapter key in unrelated work | No false cross-work duplicate |
| DUP-006 | New translation/source edition for published chapter | Correct owner policy prevents automated remake across editions |
| DUP-007 | Cancelled incomplete variant | Preserved as cancelled; no automatic resume; policy distinguishes from made episode |
| DUP-008 | Owner explicitly requests new variant | New production ID with lineage; original intact |
| DUP-009 | Worker retries after lease expiry | Idempotent claim, no two active paid jobs |
| DUP-010 | Homepage shows posted chapter as upcoming | Read-only reconciliation detects and explains mismatch |
| PUB-001 | Export rendered but not approved | Cannot create active external upload |
| PUB-002 | Wrong connected channel / OAuth identity | Block and request owner account verification |
| PUB-003 | Rights unknown/revoked/expired | Block regardless of technical QA |
| PUB-004 | Upload accepted, response lost | Mark unverified, reconcile remote ID, no blind duplicate retry |
| PUB-005 | Publishing OFF in staging | No provider upload/Drive/network write |
| PUB-006 | Owner approves private but job requests public | Reject mismatched release intent |
| PUB-007 | Stale title/package after owner edit | Old release approval invalidated |
| PUB-008 | Scheduled event triggers during deployment | No duplicate intent, safe job drain/lease recovery |
| PUB-009 | Provider returns copyright rejection | Preserve evidence, halt retries, do not switch accounts |
| PUB-010 | New platform/Drive target is not connected | No implicit fallback to another destination |

## 7. Research and performance loop

| Case | Stimulus | Pass evidence |
|---|---|---|
| RI-001 | New title outside current watchlist | Discovered with dated catalog/source evidence |
| RI-002 | Video age 1,000 days, huge lifetime views | Not labeled as high current VPH |
| RI-003 | Two observed view counts 24h apart | Correct actual interval-based velocity; unit/date retained |
| RI-004 | Only 12 bounded YouTube search hits | Competition confidence low, no exhaustive-supply claim |
| RI-005 | Repeated weekly uploads from one creator | Supply creators counted separately from total video count |
| RI-006 | Multiple unrelated results share title tokens | Ambiguous matches excluded or reviewed |
| RI-007 | Catalog rank high, no YouTube demand evidence | Reader interest and video opportunity kept distinct |
| RI-008 | Reddit provider permission unavailable | Adapter unavailable, research continues without fabricated claims |
| RI-009 | A-tier candidate has short backlog and many recent rivals | Red-team downgrade with rationale |
| RI-010 | Licenses unknown | Candidate is blocked from production/publication regardless of score |
| ANA-001 | YouTube retention ratios on 10min and 2h videos | Correct timeline mapping and sample resolution disclosed |
| ANA-002 | CTR changed after simultaneous title+thumb | No false attribution to only one component |
| ANA-003 | Competitor private watch time unavailable | `unknown`, not inferred |
| ANA-004 | Platform disconnect/delete request | Stop collection, purge restricted data per provider terms |

## 8. Real browser and operation scenarios

| Case | Interaction | Pass evidence |
|---|---|---|
| UI-001 | Research candidate → source evidence → greenlight | Same canonical work, source permissions and cost shown |
| UI-002 | Open episode text then click event | Correct original panel, OCR, speaker and matching shot highlighted |
| UI-003 | Edit script and view impact | Voice/media marked stale; precise cost/rebuild preview |
| UI-004 | Review failed final media at timestamp | Player jumps to exact final MP4 timestamp and shows source/beat |
| UI-005 | Edit owner title before queue | Owner edit persists through all background prep runs |
| UI-006 | Open page on iPhone | Video/QA review usable as tabs with accessible controls |
| UI-007 | Cancel job, restart worker | Job stays cancelled; original files unaffected |
| UI-008 | Break provider configuration midworkflow | Failure is clear, no unrelated account fallback |
| UI-009 | Browser requests stale revision | 409 conflict, no lost edits |
| UI-010 | Staging production with fake channel | No external public effects despite full simulated completion |
| OPS-001 | Restore Postgres backup | Canon+ledger+jobs+approvals consistent |
| OPS-002 | Restore object artifact | SHA matches DB manifest |
| OPS-003 | Entire staging instance deleted then recreated | Recovery runbook meets defined RPO/RTO test |
| OPS-004 | Media worker 100 failed child processes | PID/memory bounded; no queue lock leak |
| OPS-005 | Cost provider responds after timeout | Reconciliation before further charges |
| OPS-006 | API returns 429/5xx | Retry bounded, alerting and circuit breaker work |
| OPS-007 | Deploy old image with newer schema | Compatibility or safe rollback plan passes |
| OPS-008 | Restore with source copyright removal notice | Deleted restricted data not silently restored into public access |

## Gold fixture corpus and grading rubric

**Required gold corpus:** at least 12 permissioned/synthetic episodes covering (a) action and multi-panel movement, (b) dialogue and bubble-only panels, (c) two look-alike characters, (d) changing names/translations, (e) Korean text/Unicode, (f) tall scrolls/rotated layout, (g) a misleading decorative panel, (h) hard cut/cliffhanger, (i) episode with short and long beat pauses, (j) intentionally bad TTS with silent clip, (k) multi-chapter compilation and (l) metadata inherited from wrong neighboring episode. Keep corresponding original source, labeled line order, must-retain events, approved names, reference script, preferred shot sequence, failure examples and permissible editing rights.

**Review scales:** 0–5 per dimension (source fidelity, chronology, character consistency, dialogue, narration, pacing, shot relevance, audio integrity, title truth, thumbnail clarity, description/tag accuracy and audience-fit hypothesis). Ratings must have human reviewer identity/date and concrete reasons. `>=4.5/5` is an aspirational production target on sampled real episodes; technical and human dimensions are recorded separately. A video scoring 5 on technical integrity and 2 on pacing is **not** called 9/10 overall. Report sample size, blinded comparisons when feasible and disagreement instead of averaging away severe failures.

## Exit criteria before enabling unattended production

1. All P0 safety, rights, dedup, publishing, deployment-isolation and recovery cases pass.
2. Zero unresolved P0/P1 source, narration, final-media or packaging findings in the approved pilot.
3. At least three diverse complete real/published-permitted private MP4s independently watched by the owner and compared with gold examples.
4. Budget estimates and actual provider bills reconciled for each production.
5. Source authorization and platform/account identity are explicitly verified.
6. The owner affirmatively enables `PRODUCE` for named enrolled series with known caps; publishing remains separately owner approved.
