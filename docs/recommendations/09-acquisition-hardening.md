# I. Acquisition pipeline hardening

## Recommendation

Separate retrieval attempts, immutable content, extraction versions, passages and verification results.
Use structured providers first; model extraction is optional, not the default for every source.
Make “matches / changed / unreachable” a comparison to a named baseline, not a truth score.
Distinguish failed extraction from changed source content.
Retain exact quotations separately from authored summaries and repair excerpts through new source versions.
Never treat an agent-written retrieval label or metadata hash as a fetched-document record.

### Proposed tables/files

| Record | Minimum fields |
|---|---|
| `source_identity` | Stable ID, publisher, original URL, rights-policy reference; mutable URL is not a document version |
| `fetch_attempt` | UUID, source ID, requested/final URL, redirect chain, UTC start/end, method, status, safe response headers (ETag/Last-Modified/content-type), byte count, tool/version, outcome/error, snapshot hash? |
| `content_object` | SHA-256, size, media type, local object path, retention/distribution class, captured_at; write-once if permitted |
| `source_version` | ID, source identity, content hash?, publication date/precision, declared edition, retrieval attempt, previous version?, rights assessment; no invented content hash if bytes unavailable |
| `extraction_version` | ID, source version, extractor/version/config hash, text hash, page/table spans, method, OCR language/confidence, transform version |
| `evidence_passage` | ID, extraction version, exact text, offsets/page/bbox or table row+column+headers, language, optional translation with translator/version |
| `verification_result` | ID, baseline source version/hash, attempted source version, comparison scope/algorithm, state, reason, quote match mode, checked_at; append-only |

Local-only files: `objects/sha256/<prefix>/<hash>` for allowed bytes; extraction derivatives keyed by source hash + extractor/config, not by URL. Retain original/extracted hashes separately. A version may lack local bytes because redistribution/storage rights forbid retention; it must expose reduced reproducibility. Immutable history does not imply illegally retaining content forever: a later rights-driven removal leaves a tombstone/hash/metadata and records the removal, without rewriting review decisions. Do not publicly ship entire protected snapshots by default.

Acquire idempotently: first append attempt, stream with byte/time limits to a private staging file, hash bytes, atomically register object and version, then enqueue extraction. Retry with bounded backoff and conditional requests; 304 refers back to a known successful response. Crash recovery must not leave DB references to nonexistent objects. Export/backup pins a manifest of DB versions and object hashes; test restore of both.

HTTP, API and browser capture are different adapters. For script-rendered pages retain the rendered DOM and relevant permitted response artefacts, navigation URL, browser version, readiness rule and timestamp. A plain HTML shell or consent/interstitial page with HTTP 200 is not successful content acquisition. Do not bypass access controls. For scanned PDFs retain page image hash and OCR spans/confidence; a human checks the cited cells against the image. OCR substring matches prove consistency with OCR, not correctness against the scan. Text PDFs preserve layout/page locators; structured tables need headers and unit/period context, not isolated cells.

### Three-state verification without false positives

`matches`: the named baseline comparison is reproducible and equal under the stated hash/text algorithm. A raw-byte hash match is different from a normalized body-text match; neither verifies factual truth.

`changed`: comparable content was successfully obtained and differs from the baseline. A navigation/banner-only byte change may leave cited passages matching; show content drift and passage support separately. Do not infer the cause was a factual revision.

`unreachable`: could not obtain **comparable evidence**, with reason `network_error`, `access_denied`, `render_failed`, `parse_failed`, `unsupported_format` or `baseline_missing`. Display reason-specific wording (e.g. “cannot compare: original snapshot missing”), not “website offline.” Include `comparison_readiness=ready|not_ready` so missing legacy baselines cannot masquerade as tested matches. This preserves three headline outcomes while admitting that not every failure is network reachability.

For legacy sources, a newly retrieved passage may match the stored anchor but cannot prove byte identity with what the maintainer saw. No old snapshot exists. Establish a new baseline honestly; do not synthesize the earlier one from today's page.

### Four excerpt repairs: newly fetched evidence

The four cited pages were opened again. The prior audit's single explanation is overbroad: O-S05 and O-S07 currently spell out barrels per day followed by `(b/d)`; their stored excerpts omit that parenthetical. O-S08/O-S10 use the abbreviated unit. This fresh observation does not reconstruct the earlier page or disprove the earlier fetch result.

| Source | Short replacement anchor observed in fetched text | Required correction |
|---|---|---|
| [O-S05](https://www.eia.gov/todayinenergy/detail.php?id=67905) | `China imported just 8.1 million barrels per day (b/d) of crude oil in 2Q26` | Restore parenthetical; passage describes customs data. Re-review O-C07 estimate label separately rather than silently changing epistemic status |
| [O-S07](https://www.eia.gov/todayinenergy/detail.php?id=67825) | `Exports increased to 13.6 million barrels per day (b/d) in April` | Restore parenthetical; surrounding context defines crude plus products |
| [O-S08](https://www.eia.gov/todayinenergy/detail.php?id=68125) | `crude oil production averaged 13.7 million b/d` | Replace reworded quotation; preserve full-half-year locator/context separately |
| [O-S10](https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/) | `could provide about 4.7 million b/d of capacity to bypass the strait` | Preserve conditional capacity, never actual flow |

These anchors were checked against web-tool returned page text, **not archived raw HTTP snapshots**. Proposed repair procedure: fetch and retain a permitted snapshot, deterministic extraction, confirm each contiguous span plus surrounding context, add immutable replacement source-version records linked to old ones, propose evidence-reference corrections for affected claims, then review. Do not edit `evidence_sources` (immutable trigger) or overwrite old quotes. The old quote remains available in historical views with a later verification notice.

Excerpt policy: `passage_kind=verbatim|ocr_transcription|authored_summary`, verification mode, attribution and locator are mandatory. Only verified verbatim text is typeset as an exact quotation; OCR transcriptions are labelled and human-checked; authored summaries are visibly prose with no quote marks. Keep passages as short as needed for meaning, not shorter than needed to bind number to entity, unit and period. There is no universal word count that grants redistribution rights. EIA's [reuse policy](https://www.eia.gov/about/copyrights_reuse.php) should be checked for exceptions/third-party material; “all government pages can be copied wholesale” is not a safe importer rule.

### Security and operating boundary

Fetch only permitted public HTTP(S) targets; validate DNS/IP and every redirect against private/link-local/loopback ranges. Enforce byte, decompression, redirect, CPU, page and elapsed-time caps. Isolate browser/PDF parsing; strip secrets from headers/logs and never forward local credentials. Respect provider policies/rate limits. Raw page text cannot instruct the importer or model. A pack cannot select arbitrary filesystem paths, executable parsers, SQL or scripts. A hash ensures identity/integrity, not trusted authorship or licence permission.

## Evidence from the repo

`Source` records contain hand-written retrieval labels only. `storage/reviews.py` computes `content_hash` from serialized metadata. Search of `backend/app` and `scripts` for HTTP client/acquisition calls found none; fetch matches were SQL fetchone/fetchall. `EvidencePanel.tsx` wraps every excerpt in quotation marks. O-S14's URL is a mutable weekly PDF; O-S19 is documented as scanned. Copper `access-checks.json` records bounded response metadata/hashes, but its README says bodies were discarded. The “7 of 17” historic check has no retained checker; it is a documented prior observation, not a reproduced rate here.

## Options considered

| Option | Assessment |
|---|---|
| Agent writes source JSON directly | Current reproducibility problem persists |
| Snapshot + deterministic structured extraction everywhere | Prefer where possible; scans/prose still require interpretation |
| Layered acquisition/extraction/verification/review | Recommended; failures stay attributable |

## Migration and compatibility impact

Append source versions and verification records; preserve all 34 legacy source records and 44 claim/review histories. New source IDs can be added through the legacy generator where appropriate; a reviewed claim correction switches evidence references. Source-version tables and metadata-only updates require dedicated migrations/new release imports because the generator rejects edits and no-op additions. Never disable source/proposal/decision/version immutability to fix quotations. Use A's schema-version decoder and B's clocks; migration must retain the old seed fingerprint until explicit cutover.

## Risks

Snapshots can contain copyrighted/private content or become expensive. A parser may return plausible but wrong text. Changes in boilerplate can create false alarms. Successful extraction is not support; support is not physical verification.

## Effort

**L** for all HTML/browser/PDF/OCR modes; **M** for one structured/HTML source pilot. A/B and J first; H validates proposals and F consumes reviewed updates.

## Decisions needed from the user

Approve verbatim-only quotation display with separately labelled summaries and local-only, rights-controlled snapshots?

## Unverified or not checked

No acquisition code written, PDFs parsed, OCR run or raw snapshots archived. The historical 7/17 rate, original retrieval method and historical page contents remain **UNVERIFIED**. Repair anchors need snapshot-backed confirmation during implementation. No claim that all source figures are correct follows from these four text checks.
