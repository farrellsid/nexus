# Roadmap and verification plan

Proposal, 2026-09-23, for the user to reorder. The order follows the dependency graph in `docs/recommendations/00-summary.md` and the decisions in `docs/decisions.md`. Sizes (S, M, L) follow the recommendations' effort labels; no calendar estimates are given. A detailed implementation plan for a milestone is written when that milestone starts, not before.

## How to read the verification tags

- **[T]** An automated check that must pass and that anyone can run.
- **[A]** An independent check by the assistant, done as a spot check separate from whoever built the thing. Limit: the assistant's browser is a sandbox and is not the user's hardware.
- **[U]** Something only the user can verify: meaning, taste, hardware, money, legal, or accepting a claim.

**Rule: no milestone is done on an agent's word.** Each has a runnable [T] or a shown [A] artifact. This project already found excerpts reported as verbatim that were not, and a claim (O-C26) unsupported by its own evidence.

**Baseline before M0:** 38 backend tests, 8 browser workflows, `tsc`, production build, ruff and prettier all passed on 2026-09-22, and code has not changed since.

## Overview

| M | Milestone | Size | Depends on | Track |
|---|---|---|---|---|
| M0 | Repair the existing pack | S | none | Data |
| M1 | Rights and asset gate | M | none | Gate |
| M2 | Evidence model foundations | L | M0 | Data |
| M3 | Evaluation and comparability | M | M2 | Data |
| M4 | Acquisition pipeline | M | M1, M2 | Data |
| M5 | Visual shell prototype | L | M1 | UI |
| M6 | Real data in the shell | L | M2, M5 | Merge |
| M7 | Shipping geometry pilot | M | M1, M2 | Data |
| M8 | Oil guided tour | M | M3, M6 | Content |
| M9 | Static public release | M | M8, M1 | Release |
| M10 | Second industry and packs | L | M9 | Later |
| M11 | Chat layer | L | M3, M4, a model budget decision | Later |

Two tracks can run at once: **Data** (M0, M2, M3, M4) and **UI** (M5, after M1). They merge at M6. Do not run more than two at once. If you want visuals sooner, M5 can start right after M1 without waiting for the data track.

## M0. Repair the existing pack (S)

**Goal:** trust the current pack enough to build on it.

**Build:** a custom migration, because the generator refuses changes to existing records. It repairs O-C26's evidence, corrects the coverage label ("through 2026-09-10" is contradicted by later evidence), and replaces the four non-verbatim excerpts through new source versions. The excerpt check becomes a script in `scripts/`.

**Exit checks**
- [T] The excerpt script passes for every fetchable HTML source, or lists each exception with a reason.
- [T] Fresh-database and upgraded-database migration tests pass; review history row counts are identical before and after.
- [T] Existing suites stay green.
- [A] I re-fetch five repaired sources independently and compare.
- [U] Read at least three repaired excerpts next to their pages. Approve the migration SQL before it is applied. Decide the wording of the coverage label.

**Status, 2026-09-24: applied to the local database with the user's approval (excerpts read, migration 007 and the 13 proposals approved, coverage label 2026-09-16 kept). The 13 proposals are recorded as pending; M0 is complete when a reviewer accepts them.** Pre-apply backup: `.local/backups/nexus-20260924-044805-5c5d7f.dump`.
- `scripts/verify_excerpts.py` (24 tests) passes for the oil pack: every fetchable HTML source is verbatim or carries a declared reason in `investigations/excerpt-exceptions.json`. Copper is deferred to its data expansion.
- Seven replacement source versions O-S21 to O-S27 exist in the fixture, each verified as a verbatim span of the fetched page. Old versions stay; they are declared as superseded.
- `backend/app/storage/migrations/007_repair_oil_evidence_versions.sql` (hand-written) refreshes the seed and inserts the seven sources. The seed diff was checked programmatically: only `scope`, `developments_through` and the seven added sources changed.
- 13 evidence-only correction proposals are planned in `investigations/02-oil-system/repairs/2026-09-24-oil-evidence-versions.json`, recorded through `scripts/propose_evidence_repairs.py`. They stay pending until a person accepts each one.
- Rehearsed on a restored copy of the database (`nexus_rehearsal_m0`): the migration applied, all 13 proposals were recorded (57 = 44 + 13), a second run added nothing, and the real database was unchanged (44 proposals, 0 versions).
- The [A] independent re-fetch (curl and a different tag-stripper, not the verifier's code) covered O-S21, O-S23, O-S24, O-S26 and O-S27. It found that O-S21 and O-S27 used an ASCII `-` and `'` where the pages use `–` and `’`; the verifier folds those on purpose, so both excerpts were corrected to the page's exact characters and migration 007 was regenerated. O-S23 matches only ignoring whitespace in that crude stripper because the page's footnote markers are inline; the verifier's rendering model treats them the same way.
- Full backend suite (98 tests, including a persistence test that repair proposals stay pending and leave displayed claims unchanged) passes; the licence gate has 0 errors. The 4 claims still flagged for figure support (O-C02, O-C03, O-C16, O-C26) are exactly those whose proposals add the missing evidence, so they clear once accepted.
- The [U] steps are done. Remaining: a reviewer accepts or rejects the 13 pending proposals in the review panel.

## M1. Rights and asset gate (M)

**Goal:** know what may be reused and released.

**Build:** LICENSE files (MIT for code; CC BY 4.0 for original authored material), updated third-party notices, an inventory of every God's Eye asset intended for reuse (CSS, fonts, icons, images, data) with its licence, structured `rights` on sources, and a licence check script.

**Exit checks**
- [T] The check fails on an asset or pack with no verified licence.
- [A] I verify each retained asset's licence at its source and list the unverified ones as excluded.
- [U] Give the copyright holder line for the notices. Confirm the exclusions. Decide whether to take legal advice before any public release (I recommend before M9, not now).

**Gate:** the shell prototype may use only assets on the cleared list.

**Status, 2026-09-24: done, except the legal-advice decision, which waits for the M9 gate.** `LICENSE` and `LICENSE-CONTENT.md` were written with `farrellsid` as holder, and `check_licences.py --mode release` passes with 0 errors. Earlier notes follow.

**Earlier status, 2026-09-23:**
- Done: `scripts/check_licences.py` with 24 tests; `licences/components.json`, `licences/source-rights.json` (34 sources) and `licences/policy.json`; licences of the retained assets read from primary texts by the assistant (the review's findings all held).
- The gate in release mode currently fails on exactly two items: `LICENSE` and `LICENSE-CONTENT.md` do not exist.
- Waiting on the user: the copyright holder line; confirmation that `Zlib` may join the allow-list; whether to take legal advice before M9.
- Result to note: as classified today, only the 15 EIA sources may show their excerpts in a public build. The other 19 are withheld until their publishers' terms are read.

## M2. Evidence model foundations (L)

**Goal:** claims, time and measurements become filterable and comparable, without rewriting history.

**Build** (recommendations 01, 02 and 04): versioned vocabulary projection for predicate, epistemic status, content type and source class; an entity registry where legacy IDs resolve as aliases; measurement identity (measure, period, unit, definition); metric-to-entity links; temporal fields. This needs its own command, because review corrections cannot change a claim's predicate. Back up the database before migrating.

**Exit checks**
- [T] A script maps all 44 claims with no omissions or extras; every legacy ID resolves; proposals, decisions and accepted versions are unchanged; fresh and upgrade migrations pass; OpenAPI is regenerated and frontend types compile.
- [A] I argue the known semantic mismatches one by one (O-C07, O-C08, O-C12, O-C13).
- [U] Review the 44-claim mapping. It is a judgement about meaning, and only you can settle it. Approve the vocabulary lists. Choose canonical names for shared entities such as China.

**Gate:** no data adapter until this passes.

**Status, 2026-09-24: done. Approved by the user, migration 008 applied, release `nx-norm-2026-09-24` recorded and accepted (reviewer `farrellsid`). Pre-apply backup: `.local/backups/nexus-20260924-055016-8c76d4.dump`.** Details below are as of the rehearsal. Plan: `docs/superpowers/plans/2026-09-24-m2-evidence-model-foundations.md`. Review sheet: `docs/normalisation-review.md`.
- One proposed release, `nx-norm-2026-09-24` (`normalisation/releases/2026-09-24.json`), maps 44 claims, 41 sources, 45 entities (43 with a legacy ID as alias; Russia and Iran added with none) and 37 metric points onto the closed vocabulary `normalisation/vocabulary-v1.json`. Recording it changes no claim, proposal, decision or version.
- [T] `scripts/normalise.py check` proves the release covers the real packs exactly (no omissions, no extras, every code listed, temporal fields consistent with stored dates, original decimal text kept). Backend suite 173 tests, ruff, licence gate, `tsc` and all 8 browser workflows pass. The OpenAPI diff is additions only.
- [T] Rehearsed on a restored copy of the database (`nexus_rehearsal_m2`): migration 008 applied, the release recorded twice (idempotent) and accepted with a placeholder reviewer, and the hashes of every recorded-history table were identical before and after. The real database has not had migration 008 applied.
- [A] The analysis of O-C07, O-C08, O-C12, O-C13, O-C25 and the copper C11/C13 is at the foot of the review sheet. It found one new defect: C11 and C13's retained excerpts are fragments that do not state the claims, although the pages do support them (added to the deferred copper audit). It also records two deviations from the recommendations (an O-C12 scope qualifier; O-M10's third point as reported and provisional).
- [U] Done: the vocabulary lists approved, the 44-claim table reviewed, shorthand country names, Russia and Iran added to the registry, the O-C23 and O-C24 reinterpretations, O-C07 `estimated`, O-M10's third point reported and provisional, and the no-`observed` rule. On the real database the recorded-history hashes were identical before and after (57 proposals, 0 decisions, 0 versions).
- Limits: accepted corrections that change a claim's dates are not re-projected (a later release supersedes); no unit conversion exists; measurement IDs use the point's position in the reviewed release as a provenance pointer.

## M3. Evaluation and comparability (M)

**Goal:** be able to measure whether answers are supported, before any model is involved.

**Build:** executable acceptance evaluations that need no paid model, corrected oracles, and the comparability and revision-lineage model with side-by-side display data.

**Exit checks**
- [T] The suite is deterministic and covers all 26 authored questions.
- [A] I check each expected answer against its sources and flag disagreements.
- [U] Confirm each expected answer is what the product should say. You are the domain judge. Decide who marks reports as comparable (you, at first).

**Status, 2026-09-24: done and applied. The user reviewed `docs/evaluation-oracle-review.md`, found the classes reasonable and approved the comparability rules; migration 009 is applied (backup `.local/backups/nexus-20260924-061617-b23ae7.dump`, recorded-history hashes identical). All 26 cases remain `assistant_draft` until the user names which expected answers they confirm; the flagged rows (Q05, O-Q05, O-Q08, O-Q12, O-Q13) still need a choice.** Details below are as of the rehearsal. Plan: `docs/superpowers/plans/2026-09-24-m3-evaluation-and-comparability.md`. Review artifact: `docs/evaluation-oracle-review.md`.
- **Evaluation:** `evals/industry-v1/suite.json` holds 26 cases (12 copper, 14 oil), all `assistant_draft`. `scripts/evaluate.py` validates the suite, runs a dependency-free BM25 retriever with a canonical-entity boost, checks an always-abstain baseline against the answer contract, and audits expected answers against their evidence. The run is byte-for-byte deterministic. Raw result: full support on 8 of 18 fact-needing cases; the baseline meets the contract on 6 of 26.
- **[A] oracle audit:** 18 mechanical findings and 8 written findings (F1 to F8). One expected answer does not answer its question (Q05); one asserts "lower" without a comparison (O-Q05); four rest on values with no retained passage (7% in O-Q12, three O-M11 values, the 13.8 forecast, copper C09's 20%). Most are one defect class, values with no retained anchor, which M4 point-level passages fix.
- **Comparability:** `app/comparability` (candidate groups, reviewer-gated ranges that are never called confidence intervals, revision and duplicate-origin handling, forecast and reported lanes) plus append-only tables (migration `009_comparability.sql`) and read endpoints `/api/comparisons`. The packs hold no conflict set and no scope metadata, so on real data no range can appear; the behaviour is proven on synthetic reports only. No write endpoint yet.
- [T] 273 backend tests, ruff, `tsc`, prettier and all 8 browser workflows pass; the OpenAPI diff is additions only. Migration 009 was rehearsed on a restored copy (`nexus_rehearsal_m3`) with recorded-history and normalisation hashes identical. The real database has not had migration 009 applied.
- [U] Done: classes accepted, comparability rules approved. Still open: per-answer confirmation, and the choice on each flagged row. Reviewer: the user, for now.

## M4. Acquisition pipeline (M)

**Goal:** evidence enters through retrieval that can be repeated and checked.

**Build:** content-addressed local snapshots, a retrieval log, three-state verification (matches, changed, unreachable), structured providers first (the EIA and JODI endpoints have not been sampled yet), and extraction proposals that must pass the gates.

**Exit checks**
- [T] The same snapshot always gives the same extraction. The verifier states are tested with fixtures, including changed and unreachable. A rights guard blocks storing disallowed content.
- [A] I re-fetch two sources independently and compare hashes.
- [U] Approve which providers to use and what may be stored locally. Read their terms, and register for API keys if a provider requires one.

**Gate:** no automated refresh or startup fetching until this passes and an opt-in design exists.

**Status, 2026-09-24: built and applied; provider adapters not yet built.** Plan: `docs/superpowers/plans/2026-09-24-m4-acquisition-pipeline.md`. Provider facts: `docs/acquisition-providers.md`.
- **Built (`backend/app/acquisition/`):** a safe fetch (public http/https only, every redirect hop checked against private, loopback, link-local and reserved ranges, caps on bytes, redirects and time, a named outcome for every attempt); a write-once content-addressed object store with a rights guard (bytes kept only when a source's `snapshot_policy` is `store`; default `hash_only`); deterministic HTML extraction that keeps the page's own characters, with exact passage location; a three-state verifier against a named baseline (`matches`, `changed`, `unreachable` with a stated reason and `comparison_readiness`); mechanical proposal gates (verbatim span, figure present and bound to its row and position, unit and period present, plans not stated as facts, no quotation marks on summaries).
- **Storage and command:** append-only tables (migration `010_acquisition.sql`: attempts, content objects, baselines, extractions, verifications), `PostgresAcquisition`, and `scripts/acquire.py` (`fetch`, `baseline`, `verify`, `history`), the only network path. Dry run by default; one fetch per `--confirm`; no loop, no schedule, nothing at startup.
- **Rights:** every source now has a `snapshot_policy` in `licences/source-rights.json` (all `hash_only`), validated by the licence gate.
- **[T]** 382 backend tests (no test uses the network), ruff, licence gate pass. Migration 010 was rehearsed on a restored copy (`nexus_rehearsal_m4`): recorded-history and normalisation hashes were identical after two real fetches; no object files were written under `hash_only`. The real database has not had migration 010 applied.
- **[A]** Two EIA pages fetched through the tool and separately with `curl`: raw byte hashes matched in only 1 of 4 comparisons (same lengths, so something varies between fetches); extracted-text hashes matched in all 4. Recorded in `docs/acquisition-providers.md`. Not a general reproducibility claim.
- **Providers:** sampled, not integrated. EIA API v2 needs a free key (403 `API_KEY_MISSING`); its bulk index is 403. JODI CSV downloads are keyless and free, with terms not found on the page.
- **[U] Done, 2026-09-24:** providers EIA and JODI approved; every source set to `store` (private, local, fair use; publication filtered later); EIA key supplied and saved in `.local/`; migration 010 applied to the real database (backup `.local/backups/nexus-20260924-064804-f1f23b.dump`, recorded history identical). Then built the EIA and JODI parsers, key redaction and a cross-check (`docs/crosscheck-report.md`: 7 of 7 comparable pack values equal EIA's at pack precision; O-M11's August values cannot be checked yet). A survey of other sources is in `docs/acquisition-providers.md`. Then, at the user's direction: registered the three verified EIA series as sources O-S28 to O-S30 (migration 011, release r2, baselines, all verified as matches), built JSON extraction, StatCan, Sodir and GDELT parsers and `scripts/collect.py`, and probed China, Brazil, OPEC and the Energy Institute (results in `docs/acquisition-providers.md`). No current Chinese monthly crude figure was obtained; OPEC and the Energy Institute refused scripts. Still open: measurement-level source bindings, manual downloads, and a China attempt from the user's network.
- **Not built:** PDF and OCR extraction, browser rendering, provider adapters, any refresh or scheduling. The gate stands: no automated refresh or startup fetching until an opt-in design exists.

## M5. Visual shell prototype (L)

**Goal:** the God's Eye look, in a TypeScript shell, before any Nexus data.

**Build:** fork the reference, strip features in small steps, and test after every removal (commit per step so the last good state is recoverable). Dark theme, globe behind, static corner readouts, the action-verb skeleton, the 2D fallback, and basic share links. Only the current oil stops as fixture data.

**Exit checks**
- [T] A smoke e2e passes after each strip step (renders, no console errors). A script asserts there is exactly one `@cesium/engine` in the dependency tree. Bundle contents match the cleared asset list.
- [A] I capture screenshots in my browser, with the sandbox limit noted.
- [U] Open it in your real Edge on your machine. Judge look, feel and frame rate on your GPU. Decide which effects (bloom, sensor looks) stay. Check reduced-motion behaviour.

## M6. Real data in the shell (L)

**Goal:** the inspector, evidence drawer, warning vocabulary, network view and numbers view, on real data.

**Build:** an adapter to the FastAPI backend; parity with today's features using the checklist in `docs/ui-flows.md` section 3.

**Exit checks**
- [T] Contract tests pass. A test walks the rendered page and asserts every figure shows unit, period, status and a source. An unresolved entity renders "NO FIX", never a guessed point. The existing eight browser workflows have equivalents.
- [A] I compare ten random rendered figures against their sources.
- [U] Check five figures yourself. Judge whether warnings are clear without being noisy. Decide which old features may be dropped.

## M7. Shipping geometry pilot (M)

**Goal:** a small corridor subset that shows alternatives honestly.

**Build:** a small sourced network (for example Suez, Cape and Malacca), modelled alternatives as separate paths, and legend text distinguishing modelled, reported and observed.

**Exit checks**
- [T] The land-crossing sampling check I ran by hand becomes an automated test. Every geometry has a source and rights record.
- [A] I verify each dataset's licence file.
- [U] Judge the rendered lanes. Approve the "modelled, not observed" wording. Accept or reject each dataset's licence outcome.

## M8. Oil guided tour (M)

**Goal:** the first complete industry tour.

**Build:** the chapter model with numeric slots, pinned releases, and the oil tour. The "student opportunities" chapter is labelled as interpretation.

**Exit checks**
- [T] Every number resolves from a slot. A superseded claim flags its chapter. **The build fails if any cited claim is not accepted.**
- [A] I trace each sentence to a claim ID and list unsupported ones.
- [U] Accept the claims in the review queue. Only you can. Approve the narrative. Settle contested points such as geopolitics, shown as attributed viewpoints.

## M9. Static public release (M)

**Goal:** a read-only public snapshot.

**Build:** an exporter (accepted evidence only, no write capability), a licence manifest, a Natural Earth globe by default, and hosting on a free static host.

**Exit checks**
- [T] A bundle scan finds no keys, private snapshots, write endpoints or uncleared assets. The licence manifest is complete. It loads with no backend.
- [A] I build it from a clean checkout.
- [U] Take legal advice if you chose to. Set up the domain and hosting. Check cost in CAD including tax. Read it once as a stranger would.

## Later

**M10** proves the pack mechanics with a second industry, likely copper. **M11** adds chat, and needs M3, M4 and a model budget decision first.

## Where your time goes

These recur, and only you can do them:
1. **Meaning:** the claim mapping (M2), expected answers (M3), tour text (M8).
2. **Accepting claims** in the review queue (M8). Nothing is publishable before this.
3. **Feel on your own hardware** (M5, M6).
4. **Money, licences and legal** (M1, M9).
5. **Provider terms and keys** (M4).

The heaviest review loads are M2's 44-claim mapping and M8's acceptance queue.

## Rules for every milestone

- It ends with tests green, the development log, status and decision log updated, and your commit.
- If a milestone exposes a design flaw, stop and update `docs/decisions.md` before continuing.
- Nothing here authorises deployment, model spend, scheduled fetching or public release.
