# M4 Acquisition Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline). Steps use checkbox (`- [ ]`) syntax. **Commits are made only when the user asks; there are no commit steps.** Each task ends with a checkpoint line in `docs/development-log.md`.

**Goal:** Evidence enters through retrieval that can be repeated and checked: an attempt is logged, content is stored by hash where rights allow, extraction is deterministic, and verification against a named baseline ends in `matches`, `changed` or `unreachable` with a stated reason.

**Architecture:** A pure domain package `app/acquisition` (safe fetch with an injectable transport, content-addressed snapshot store with a rights guard, deterministic HTML extraction and passage location, three-state verifier, proposal gates) and append-only tables plus a storage class for the log. A single opt-in command `scripts/acquire.py` is the only thing that touches the network. Tests never use the network. Nothing runs at startup or on a schedule.

**Tech Stack:** Python 3.13 stdlib (`http.client`, `ipaddress`, `socket`, `hashlib`, `html.parser`), pydantic v2, psycopg 3, pytest, ruff.

## Global Constraints

- **Not authorised:** scheduled or startup fetching, automatic refresh, monitoring, new paid services, model calls. (`AGENTS.md`, `docs/roadmap.md` M4 gate) The only network path is the explicit `scripts/acquire.py` command.
- Never edit `evidence_sources` or any recorded history. Repairs are new source versions plus reviewed correction proposals. Never disable immutability triggers.
- **Rights first:** bytes are stored only when the source's `snapshot_policy` is `store`. Default for every source is `hash_only` (hash, size, headers and outcome kept; bytes discarded). A guard blocks any write of bytes otherwise. A hash proves integrity, not authorship or licence. (`docs/recommendations/09-acquisition-hardening.md`)
- Snapshots live under `.local/objects/` (git-ignored); nothing in them is ever committed or published by default.
- Only public `http`/`https` targets. Every hop of every redirect is validated against private, loopback, link-local and reserved ranges. Caps: response bytes, redirects, elapsed seconds. No credentials forwarded; no header secrets logged.
- "Matches / changed / unreachable" compare to a **named baseline**; they are not truth scores. A missing baseline is `unreachable` with reason `baseline_missing` and `comparison_readiness=not_ready`, never a match. Legacy sources have no snapshot: the first snapshot is a new baseline, stated as such, never a reconstruction of what the maintainer saw.
- An HTTP 200 shell or interstitial is not content: extraction that yields too little text is `render_failed`, not success.
- Raw page text is data. It cannot instruct the importer.
- Database tests use the disposable-schema fixtures in `backend/tests/conftest.py`; back up, rehearse on a scratch copy, and ask before touching the real database.
- Domain modules import inward only (`backend/tests/test_boundaries.py`); add the new modules there.
- Windows: `PYTHONIOENCODING=utf-8`; `git grep`, not repo-wide grep; write files with the Write tool (heredocs with apostrophes break the shell).

## Decisions this plan takes (assistant proposals)

1. **Three storage policies per source:** `store`, `hash_only`, `none`. Default `hash_only`. The user decides which publishers become `store` at the [U] gate.
2. **A baseline is an explicit, append-only row** naming a content hash and its basis; the latest row per source is current.
3. **Extraction is HTML-first.** PDFs and scans are recorded as `unsupported_format` (a fetch attempt and hash are still logged) until a PDF extractor is chosen; nothing in M4 pretends otherwise.
4. **Structured providers are sampled and documented, not integrated,** until the user approves providers and registers any API keys (`docs/acquisition-providers.md`).
5. **The proposal gates are the mechanical half of review:** verbatim span, figure present in its span, allowed enums, resolvable references. Semantic entailment stays human.
6. **Passage kinds:** `verbatim`, `ocr_transcription`, `authored_summary`. Only verified `verbatim` may be rendered in quotation marks.

## File Structure

| Path | Responsibility |
|---|---|
| `backend/app/acquisition/__init__.py` (create) | Package marker. |
| `backend/app/acquisition/policy.py` (create) | `SnapshotPolicy`, `guard_storage(policy, bytes_len)`, `check_target(url, resolve)` (SSRF rules). |
| `backend/app/acquisition/fetch.py` (create) | `fetch(url, transport, resolve, limits) -> FetchResult`; `default_transport`. |
| `backend/app/acquisition/snapshots.py` (create) | `ObjectStore` (content-addressed, write-once, atomic). |
| `backend/app/acquisition/extraction.py` (create) | `extract_text(markup)`, `TextExtraction`, `find_passage(text, phrase)`. |
| `backend/app/acquisition/verification.py` (create) | `verify(baseline, attempt, passages) -> Verification`. |
| `backend/app/acquisition/proposals.py` (create) | `ExtractionProposal`, `gate_proposal(...)`. |
| `backend/app/storage/migrations/010_acquisition.sql` (create) | Append-only log tables. |
| `backend/app/storage/acquisition.py` (create) | `PostgresAcquisition`. |
| `scripts/acquire.py` (create) | `fetch`, `verify`, `baseline` commands; the only network path. |
| `licences/source-rights.json` (modify) | Add `snapshot_policy` per source (all `hash_only`). |
| `scripts/check_licences.py` (modify) | Validate `snapshot_policy` values. |
| `docs/acquisition-providers.md` (create) | Sampled provider facts and the [U] decisions. |
| `backend/tests/test_acquisition_*.py` (create) | One module per layer. |

---

### Task 1: Target policy, storage guard and safe fetch

**Files:** Create `backend/app/acquisition/{__init__,policy,fetch}.py`; Test `backend/tests/test_acquisition_fetch.py`.

**Interfaces:**
- `SnapshotPolicy = Literal["store","hash_only","none"]`.
- `check_target(url: str, resolve: Callable[[str], list[str]]) -> str | None`: `None` if allowed, else a reason. Rejects non-http(s), userinfo in the URL, hosts that resolve to any private, loopback, link-local, multicast, reserved or unspecified address, and literal IPs in those ranges.
- `guard_storage(policy: SnapshotPolicy) -> bool`: `True` only for `store`.
- `Limits(max_bytes=5_000_000, max_redirects=5, timeout_seconds=25)`.
- `RawResponse(status: int, headers: dict[str,str], body: bytes, truncated: bool)`; `Transport = Callable[[str, float, int], RawResponse]` (url, timeout, max_bytes; never follows redirects).
- `FetchResult(source_url, final_url, redirect_chain: list[str], status: int|None, content_type: str|None, etag: str|None, last_modified: str|None, byte_count: int, sha256: str|None, body: bytes, outcome: Literal["ok","access_denied","network_error","blocked_target","too_large","too_many_redirects"], error: str|None, started_at, ended_at)`.
- `fetch(url, transport, resolve, limits=Limits(), clock=...) -> FetchResult`: validates the target and every redirect `Location` (absolute or relative, resolved against the current URL); 401/403/451 map to `access_denied`; 5xx, timeouts, transport exceptions to `network_error`; a body longer than `max_bytes` (or `truncated`) to `too_large` with no hash; the hash is over the exact bytes received.
- `default_transport`: `http.client`, streaming read capped at `max_bytes + 1`, `User-Agent: nexus-acquire/0.1`, no cookies, no auth headers.

- [ ] **Step 1: Failing tests** with a scripted fake transport and resolver: allowed public URL returns `ok` with the sha256 of the body; `http://127.0.0.1`, `http://[::1]`, `http://10.0.0.5`, `http://169.254.169.254/latest`, `file:///etc/passwd`, `ftp://x`, and `https://user:pw@example.org/` are `blocked_target`; a hostname resolving to a private address is blocked; a redirect to a private address is blocked at that hop and the chain is recorded; a relative redirect resolves correctly; more than 5 redirects gives `too_many_redirects`; 403 gives `access_denied`; 503 and an exception give `network_error`; oversize gives `too_large` and no hash; `guard_storage` is true only for `store`.
- [ ] **Step 2 to 4:** red, implement, green; ruff; boundary entries (`acquisition/policy`: `set()`, `acquisition/fetch`: `{"acquisition.policy"}`).
- [ ] **Step 5: Checkpoint.**

### Task 2: Content-addressed object store

**Files:** Create `backend/app/acquisition/snapshots.py`; Test `backend/tests/test_acquisition_snapshots.py`.

**Interfaces:** `ObjectStore(root: Path)`; `put(data: bytes, policy: SnapshotPolicy) -> StoredObject | None`: returns `None` (writing nothing) unless the policy is `store`; otherwise writes `objects/sha256/<first2>/<sha256>` via a temporary file and `os.replace`, is idempotent for identical bytes, and refuses to overwrite a path whose content hashes differently. `get(sha256) -> bytes | None` re-hashes on read and raises `IntegrityError` if the file no longer matches. `StoredObject(sha256, size, path)`.

- [ ] **Step 1: Failing tests** (tmp_path): `hash_only` and `none` write nothing; `store` writes the expected path; a second put is a no-op; corrupting the file makes `get` raise; two different byte strings never share a path; no temporary files remain after a put; `get` of an unknown hash is `None`.
- [ ] **Step 2 to 4:** red, implement, green, lint.
- [ ] **Step 5: Checkpoint.**

### Task 3: Deterministic extraction and passage location

**Files:** Create `backend/app/acquisition/extraction.py`; Test `backend/tests/test_acquisition_extraction.py`.

**Interfaces:** `EXTRACTOR = "nexus-html-text/1"`; `extract_text(markup: str) -> TextExtraction(text: str, text_sha256: str, extractor: str, readable: bool)`: visible text with scripts, styles and templates removed, block tags as spaces, entities decoded, whitespace collapsed, and **case, quotes and dashes preserved** (unlike the verifier's folding); `readable` is false below 200 characters. `find_passage(text: str, phrase: str) -> Passage | None` returns the exact span `Passage(start, end, text)`; matching folds only whitespace (a passage must otherwise equal the page's own characters). `locate_passages` is not needed.

- [ ] **Step 1: Failing tests:** the same markup always gives the same `text_sha256` (run twice, and after re-encoding whitespace-only differences); `<script>` content is excluded; `<sup>` footnote markers stay inline while `<br>` and block tags become spaces; an en dash and a curly apostrophe are preserved; an interstitial page under 200 characters is `readable=False`; `find_passage` returns the exact original-case span with correct offsets and `None` when a dash differs (proving no folding); a passage spanning a line break is found.
- [ ] **Step 2 to 4:** red, implement, green, lint.
- [ ] **Step 5: Checkpoint.**

### Task 4: Three-state verification

**Files:** Create `backend/app/acquisition/verification.py`; Test `backend/tests/test_acquisition_verification.py`.

**Interfaces:**
- `Baseline(sha256: str, text_sha256: str | None, basis: str)`; `Attempt(outcome, sha256: str | None, extraction: TextExtraction | None, media_type: str | None)`.
- `Verification(state: Literal["matches","changed","unreachable"], reason: str, comparison_readiness: Literal["ready","not_ready"], byte_match: bool | None, text_match: bool | None, passages: list[PassageCheck])`, `PassageCheck(phrase, found: bool)`.
- `verify(baseline: Baseline | None, attempt: Attempt, phrases: list[str]) -> Verification`:
  - no baseline gives `unreachable`, `baseline_missing`, `not_ready`;
  - attempt outcomes `network_error`, `access_denied` (and blocked or too large) give `unreachable` with that reason;
  - a media type that is not HTML gives `unreachable`, `unsupported_format`;
  - an unreadable extraction gives `unreachable`, `render_failed`;
  - otherwise `matches` if the raw hash is equal **or** the text hash is equal (recording which), else `changed`; passage support is reported separately (a byte change with all passages found is `changed` with `passages` all found, never a failed claim).

- [ ] **Step 1: Failing tests** (fixtures only): each state and reason above; equal bytes; equal text with different bytes is `matches` with `byte_match=False, text_match=True`; changed text with all passages still present; changed text with a missing passage; `baseline_missing` is never `matches`; the reason wording is specific (never "offline").
- [ ] **Step 2 to 4:** red, implement, green, lint.
- [ ] **Step 5: Checkpoint.**

### Task 5: Proposal gates

**Files:** Create `backend/app/acquisition/proposals.py`; Test `backend/tests/test_acquisition_proposals.py`.

**Interfaces:** `ExtractionProposal(source_id, passage_kind: Literal["verbatim","ocr_transcription","authored_summary"], excerpt: str, locator: str, claim_statement: str, figures: list[str], unit: str | None, period: str | None)`; `gate_proposal(proposal, extraction: TextExtraction, known_source_ids: set[str]) -> list[str]` returns rejection reasons: unknown source; blank locator; `verbatim` whose excerpt is not an exact span of the extraction text (via `find_passage`); a `verbatim` excerpt containing a figure the statement does not; a statement figure absent from the excerpt; a figure whose adjacent unit or period token is missing when `unit` or `period` is stated; `authored_summary` presented with quotation marks; `ocr_transcription` without a stated review step. Empty means the proposal may enter review; it never means the claim is entailed.

- [ ] **Step 1: Failing tests** including the recommendation 08 negatives on synthetic text: changed numeral, correct numeral in the wrong row (a table row fixture where the figure exists but not next to the named entity), wrong unit, plan stated as actual (statement says "produced", excerpt says "expected"), and an instruction-like sentence in the page that must not alter the result.
- [ ] **Step 2 to 4:** red, implement, green, lint; boundary entries.
- [ ] **Step 5: Checkpoint.**

### Task 6: Migration 010 and storage

**Files:** Create `backend/app/storage/migrations/010_acquisition.sql`, `backend/app/storage/acquisition.py`; Test `backend/tests/test_acquisition_postgres.py`.

**Schema** (append-only via `prevent_history_rewrite()`): `fetch_attempt(id uuid PK, source_id text REFERENCES evidence_sources(id), requested_url, final_url, redirect_chain jsonb, started_at, ended_at, status int, content_type, etag, last_modified, byte_count bigint, tool text, outcome text CHECK (...), error text, sha256 text)`; `content_object(sha256 text PK, size bigint, media_type text, stored boolean, captured_at)` (`stored` is false for hash-only); `source_baseline(id uuid PK, source_id, sha256, text_sha256, basis text NOT NULL, reviewer text NOT NULL, supersedes_id uuid NULL UNIQUE, recorded_at)`; `extraction_version(id uuid PK, sha256, extractor text, text_sha256, readable boolean, created_at, UNIQUE (sha256, extractor))`; `verification_result(id uuid PK, source_id, attempt_id uuid REFERENCES fetch_attempt(id), baseline_id uuid REFERENCES source_baseline(id), state text CHECK, reason text, comparison_readiness text CHECK, byte_match boolean, text_match boolean, passages jsonb, checked_at)`.

**Interfaces:** `PostgresAcquisition(database)` with `log_attempt(source_id, result: FetchResult, stored: bool) -> UUID` (also records the `content_object` row when a hash exists), `set_baseline(source_id, sha256, text_sha256, basis, reviewer, supersedes=None) -> UUID` (basis and reviewer required; a second current baseline needs `supersedes`), `current_baseline(source_id)`, `record_extraction(sha256, extraction)` (idempotent), `record_verification(...) -> UUID`, `history(source_id)`.

- [ ] **Step 1: Failing tests:** attempts are logged for every outcome including `blocked_target` (no hash); the content object is recorded with `stored=False` for hash-only; blank basis or reviewer refused; a baseline supersede chain works and the latest is current; extraction recording is idempotent; verification rows reference their attempt and baseline; every new table is append-only; recorded-history hashes (sources, proposals, decisions, versions, normalisation, comparison) are identical after writes; unknown source raises.
- [ ] **Step 2 to 4:** red, implement, green, lint; full suite.
- [ ] **Step 5: Checkpoint.**

### Task 7: The opt-in command and the rights field

**Files:** Create `scripts/acquire.py`; Modify `licences/source-rights.json`, `scripts/check_licences.py`, `backend/tests/test_licence_check.py`; Test `backend/tests/test_acquire_command.py`.

`scripts/acquire.py` commands: `fetch SOURCE_ID [--confirm]` (dry run by default: prints the URL, the policy and what would be stored; with `--confirm` performs one fetch, logs the attempt, stores bytes only when the policy is `store`, extracts, and records the extraction), `baseline SOURCE_ID --attempt ATTEMPT_ID --reviewer NAME --basis TEXT`, `verify SOURCE_ID [--confirm]` (fetches once and compares to the current baseline, checking the source's stored excerpt as the passage), `history SOURCE_ID`. It refuses to run without a configured database. It never loops, sleeps or schedules.
`check_licences.py` requires every source's `snapshot_policy` to be one of the three values; the rights sidecar gains `"snapshot_policy": "hash_only"` for all 41 sources.

- [ ] **Step 1: Failing tests:** a dry run performs no fetch and no write (fake transport asserts it is never called); `--confirm` with a fake transport logs one attempt and, for a `hash_only` source, stores no object file; for a `store` source it stores one; `verify` with no baseline reports `baseline_missing`; the licence check rejects an unknown policy value.
- [ ] **Step 2 to 4:** red, implement, green, lint.
- [ ] **Step 5: Checkpoint.**

### Task 8: Provider sampling, independent hash check, rehearsal and documentation

- [ ] **Step 1: Sample the structured providers** (read-only HTTP, no keys, no storage): the EIA Open Data API v2 root and bulk-download index, and JODI's downloadable files. Record in `docs/acquisition-providers.md`: URL, whether a key is required, format, licence or terms link, size, update cadence as stated, and what it could replace in the packs (for example STEO chokepoint tables, JODI country production). Do not build adapters. List the decisions the user must make (providers, keys, what may be stored).
- [ ] **Step 2: [A] independent check.** Pick two static sources (for example two EIA Today in Energy articles). Fetch each through `scripts/acquire.py fetch --confirm` (policy `hash_only`) and separately with `curl`; compare SHA-256 of the response bodies. Record equal, or the reason they differ (for example dynamic content). Do not claim reproducibility beyond what the comparison shows.
- [ ] **Step 3: Full checks** (suite, ruff, licence gate, `tsc`, browser workflows) and **rehearse migration 010** on a restored scratch copy of a fresh backup; recorded-history hashes must be identical.
- [ ] **Step 4: Docs:** `docs/roadmap.md` (M4 status), `docs/decisions.md`, `docs/development-log.md`, `docs/development-status.md`, `docs/data-acquisition.md` (built versus proposed), README (new commands), this plan's "As built".
- [ ] **Step 5: Stop and ask the user** ([U]): approve providers and storage policy per publisher, read the terms, register for API keys if needed. On approval, back up and apply migration 010 to the real database.

## As built (deviations from this plan)

- `FetchResult` outcomes include `http_error` (a 4xx other than 401, 403, 451) in addition to the plan's list.
- `stored` is recorded on `fetch_attempt`, not `content_object`, so a later `store` fetch of already-seen content cannot contradict an earlier hash-only row.
- `ExtractionProposal` gained `entity` and `figure_position`, because "the right numeral in the wrong row" cannot be caught without saying which number after which entity the figure is.
- `PostgresAcquisition` gained `attempts`, `verifications` and `extraction_text_hash`, which the command needs.
- The command's core functions (`do_fetch`, `do_verify`, `do_baseline`) take injected transport, resolver, store and database so tests run offline.
- No API endpoints were added in M4, so the OpenAPI contract is unchanged.
- The [A] hash check used a scratch database copy so the real database was not touched.

## Self-review

- **Roadmap M4 coverage:** content-addressed snapshots: Task 2. Retrieval log: Task 6. Three-state verification: Task 4. Structured providers first: Task 8 (sampling, no adapters). Extraction proposals that must pass gates: Task 5. Exit [T] same snapshot gives the same extraction: Task 3; verifier states with fixtures including changed and unreachable: Task 4; rights guard blocks storing: Tasks 1, 2 and 7. [A] two independent fetches compared by hash: Task 8 step 2. [U]: Task 8 step 5. Gate (no automated refresh, no startup fetching): the only network path is the explicit command; tests use a fake transport.
- **Placeholders:** none in code tasks; every interface lists signatures and every test list is specific. Provider facts are gathered in Task 8, not assumed.
- **Names:** `SnapshotPolicy`, `FetchResult`, `ObjectStore`, `TextExtraction`, `Passage`, `Verification`, `Baseline`, `Attempt`, `ExtractionProposal`, `PostgresAcquisition` are used consistently.
- **Limits, stated:** DNS-rebinding between validation and connection is not fully closed by a stdlib client (documented, low risk for a local opt-in tool); PDFs and scans are not extracted; no browser rendering; structured-provider adapters wait for the user's approval and keys.
