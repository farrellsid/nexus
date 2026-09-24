# M3 Evaluation and Comparability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline). Steps use checkbox (`- [ ]`) syntax. **Commits are made only when the user asks; there are no commit steps.** Each task ends with a checkpoint line in `docs/development-log.md`.

**Goal:** Be able to measure whether answers are supported before any model exists (deterministic evaluation of all 26 authored questions), and represent disagreement between reports as reviewed, append-only comparability data with side-by-side display data.

**Architecture:** Two new domain packages. `app/evaluation` holds the eval-case schema and validator, a dependency-free lexical retriever over claims, measurements and sources, an answer contract with a checker, and an oracle audit that flags figures in expected answers that no required record supports. `app/comparability` holds pure rules that group candidate reports, and a builder that turns reviewed memberships and relations into side-by-side cards. A hand-written migration adds append-only tables for comparison sets, memberships and claim relations. No paid model, no network, no writes to recorded claims.

**Tech Stack:** Python 3.13 / pydantic v2 / psycopg 3 / FastAPI / PostgreSQL (existing); pytest + ruff; `openapi-typescript`.

## Global Constraints

- The 26 acceptance records and the 44 claims are never edited. Eval cases reference their IDs. (`docs/recommendations/08-evaluation-and-trust.md`)
- Expected answers are **drafts of the oracle**, not ground truth; scoring never rewards reproducing `expected_answer` text. The retriever must not see expected IDs or answer text.
- Counts are raw (for example 18 of 26), never percentages that imply generalisation. Failed cases are listed, never averaged away.
- Synthetic fixtures are clearly marked "Synthetic test data" and live only in tests. No fabricated second provider for O-M11 or any other real measurement.
- A range is shown only after a reviewer marks reports comparable; it is never called a confidence interval, never averaged, never mixes forecast with reported lanes, and never counts a revision or a shared origin as an independent report. Missing metadata means unresolved, not equal. (`docs/recommendations/03-conflicting-sources.md`)
- Reviewer name is required on every comparability decision. Initially the user is the only reviewer (`docs/roadmap.md`, M3 [U]).
- Tests must not write to the production database: database tests use the disposable-schema fixtures in `backend/tests/conftest.py`.
- Domain modules import inward only (`backend/tests/test_boundaries.py`); the new packages are added to that rule.
- Back up before any migration; rehearse on a restored scratch copy; ask the user before touching the real database.
- Windows: `PYTHONIOENCODING=utf-8`; `git grep`, not repo-wide grep.

## Decisions this plan takes (assistant proposals)

1. **Record references are `kind:id`** strings: `claim:O-C02`, `measurement:<case>:<metric>:<n>`, `source:O-S05`. All IDs are unique across the two packs, so no case prefix is needed for claims and sources.
2. **The retriever is BM25 over three record kinds**, written by hand (no dependency), plus a canonical-entity boost from the accepted release's aliases. Vectors stay deferred until a measured miss justifies them.
3. **The answer contract is structured**, so a future model adapter replaces only the answerer. M3 ships an always-abstain baseline to prove the harness scores something.
4. **Oracle status per case** is `assistant_draft` until the user confirms it; the suite reports how many are confirmed.
5. **Comparison sets are user-created and reviewer-attributed**; nothing is auto-marked comparable. The machine only proposes *candidate groups* (same key, at least two distinct origin groups).
6. **No write endpoint yet.** Assessments are recorded through the storage class (and later a CLI or the M5 shell), so the "who marks reports" decision is enforced by the required reviewer field, not by a new UI.

## File Structure

| Path | Responsibility |
|---|---|
| `backend/app/evaluation/__init__.py` (create) | Package marker. |
| `backend/app/evaluation/cases.py` (create) | `EvalCase`, `EvalSuite`, `validate_suite(...)`. |
| `backend/app/evaluation/figures.py` (create) | `figures_in(text)`, `unsupported(figures_text, support_texts)`. |
| `backend/app/evaluation/corpus.py` (create) | `Corpus`, `Record`, `build_corpus(investigations, measurements)`. |
| `backend/app/evaluation/retrieval.py` (create) | `retrieve(corpus, question, k)`, `score_retrieval(case, hits, k)`. |
| `backend/app/evaluation/answers.py` (create) | `Answer`, `check_answer(...)`, `AlwaysAbstain`. |
| `backend/app/evaluation/oracle.py` (create) | `oracle_findings(case, corpus, expected_answer)`. |
| `backend/app/comparability/__init__.py`, `model.py`, `display.py` (create) | Reports, keys, candidate groups, memberships, relations, `build_display`. |
| `backend/app/comparability/reports.py` (create) | `build_reports(measurements, investigations, vocabulary)`. |
| `backend/app/storage/migrations/009_comparability.sql` (create) | Append-only comparison tables. |
| `backend/app/storage/comparisons.py` (create) | `PostgresComparisons`. |
| `backend/app/main.py` (modify) | Read endpoints `/api/comparisons`, `/api/comparisons/{id}`. |
| `evals/industry-v1/suite.json` (create) | The 26 eval cases. |
| `scripts/evaluate.py` (create) | `check`, `run`, `oracle` commands. |
| `docs/evaluation-oracle-review.md` (create) | The [A] and [U] artifact: each expected answer against its sources. |
| `backend/tests/test_evaluation_*.py`, `test_comparability_*.py` (create) | One module per layer. |

---

### Task 1: Figure extraction and the eval-case schema

**Files:** Create `backend/app/evaluation/{__init__,figures,cases}.py`; Test `backend/tests/test_evaluation_cases.py`.

**Interfaces:**
- `figures_in(text: str) -> list[str]`: numeric tokens that are not dates: `13.7`, `51.24`, `1,234`, and integers directly before `%`, `million`, `billion` or `thousand`. `2026-Q2`, `2025`, `2026-09-11` are not figures.
- `unsupported(text: str, support_texts: list[str]) -> list[str]`: figures in `text` absent from every support text, compared with thousands separators removed.
- `EvalCase(id, answer_class: Literal["supported","partial","unknown"], required_claims: list[str], required_measurements: list[str], required_sources: list[str], context_claims: list[str], required_qualifiers: list[str], prohibited_assertions: list[str], expected_entities: list[str], oracle_review_status: Literal["assistant_draft","user_confirmed"], split: Literal["development","held_out"], notes: str)`.
- `EvalSuite(suite_id, version, release_id, cases: list[EvalCase])`.
- `validate_suite(suite, acceptance_ids: set[str], claim_ids, measurement_ids, source_ids, entity_ids) -> list[str]`: every acceptance ID has exactly one case and no case is unknown; every reference resolves; a `supported` case requires at least one required claim or measurement; an `unknown` case may not list required facts (context goes in `context_claims`); `partial` needs at least one required qualifier; no duplicate IDs.

- [ ] **Step 1: Write failing tests** for each rule above, with a small synthetic suite fixture (for example `figures_in("Iraq 3.86 million b/d in 2026-Q2 and 7% below") == ["3.86", "7"]`, `unsupported("3.86 and 9.99", ["Iraq at 3.86"]) == ["9.99"]`, and one test per validation rule asserting the problem text).
- [ ] **Step 2: Run, confirm failure** (`ModuleNotFoundError: app.evaluation`).
- [ ] **Step 3: Implement** `figures.py` (regexes adapted from `scripts/verify_excerpts.py`; the script is left unchanged) and `cases.py`.
- [ ] **Step 4: Run tests and ruff; add `evaluation/figures`, `evaluation/cases` to the boundary rule** (allowed: `knowledge`, `evaluation.figures`).
- [ ] **Step 5: Checkpoint.**

### Task 2: Corpus and the lexical retriever

**Files:** Create `backend/app/evaluation/{corpus,retrieval}.py`; Test `backend/tests/test_evaluation_retrieval.py`.

**Interfaces:**
- `Record(ref: str, kind: Literal["claim","measurement","source"], text: str, entities: list[str])`.
- `Corpus(records: list[Record], entity_names: dict[str, list[str]])` where `entity_names` maps canonical entity ID to its names and legacy IDs' names.
- `build_corpus(investigations, release) -> Corpus`: claims (statement, caveat, predicate, endpoint names), measurements (metric title, pack label, value, measure name, entity name), sources (title, publisher, locator, excerpt).
- `retrieve(corpus, question, k=10) -> list[Hit]`, `Hit(ref, score)`: BM25 (k1=1.5, b=0.75) over lowercased alphanumeric tokens with a short stop-word list, plus a fixed boost for records whose entities are named in the question. Deterministic: ties broken by `ref`.
- `score_retrieval(case, hits, k) -> RetrievalScore(found: list[str], missing: list[str], recall: tuple[int,int], first_relevant_rank: int|None, full_support: bool)` over required claims and measurements (sources reported separately).

- [ ] **Step 1: Failing tests:** synthetic corpus of five records; the record containing all query terms ranks first; identical scores order by `ref` (determinism: two calls equal); the entity boost lifts a record naming the queried entity; `score_retrieval` reports found and missing correctly and `full_support` only when nothing is missing; an empty required list yields `recall (0, 0)` and `full_support True` (nothing to find).
- [ ] **Step 2 to 4:** confirm red, implement, green, lint, boundary rule entries.
- [ ] **Step 5: Checkpoint.**

### Task 3: Answer contract and checker

**Files:** Create `backend/app/evaluation/answers.py`; Test `backend/tests/test_evaluation_answers.py`.

**Interfaces:**
- `Fact(text: str, cites: list[str])`; `Answer(abstained: bool, facts: list[Fact], limitation: str = "")`.
- `check_answer(case: EvalCase, answer: Answer, corpus: Corpus) -> list[str]` returns violations:
  - a citation that is not a record in the corpus;
  - an `unknown` case answered without abstaining;
  - a `supported` case that abstains, or that fails to cite every required claim and measurement;
  - a figure in any fact that appears in none of that fact's cited records (`unsupported`);
  - a prohibited assertion (case-insensitive substring) in any fact text or the limitation;
  - a missing required qualifier (case-insensitive substring across all fact and limitation text) when the answer does not abstain.
- `AlwaysAbstain.answer(case, question, hits) -> Answer(abstained=True, ...)`: the baseline.

- [ ] **Step 1: Failing tests, one per violation,** plus the **synthetic negative fixtures** from recommendation 08: changed numeral, correct numeral cited to the wrong record, plan stated as actual (a prohibited assertion), missing qualifier, and an injected instruction inside a fact text that must be treated as data (the checker flags only what its rules say). A test asserts a fully correct synthetic answer returns `[]`.
- [ ] **Step 2 to 4:** red, implement, green, lint.
- [ ] **Step 5: Checkpoint.**

### Task 4: Author the suite and the oracle audit

**Files:** Create `evals/industry-v1/suite.json`, `backend/app/evaluation/oracle.py`, `scripts/evaluate.py`; Tests `backend/tests/test_evaluation_oracle.py`, `test_evaluation_suite.py`.

**Interfaces:**
- `oracle_findings(case, corpus, expected_answer) -> list[str]`: figures in the expected answer that no required (or context) record's text supports.
- `scripts/evaluate.py check` validates the suite against the real packs and accepted release (no database needed: the release JSON is used directly); `run --k 10` prints validation, per-case retrieval raw counts, the always-abstain baseline outcome per case, the negative-fixture results, and exits 1 only on an invalid suite or a checker that fails to reject a negative fixture; `oracle` prints `oracle_findings` for every case.

- [ ] **Step 1: Failing tests:** `oracle_findings` flags `9.99` when no required record contains it and returns `[]` when supported; `test_evaluation_suite.py` loads the real suite and asserts `validate_suite` returns `[]`, exactly 26 cases (12 copper, 14 oil), and every case's `oracle_review_status` is `assistant_draft` until the user confirms (a test that counts them, so confirmation is visible in the diff).
- [ ] **Step 2: Author the 26 cases.** For each acceptance case read the stored expected answer, the cited claims and their excerpts, and recommendation 08's table. Required refs follow that table: Q01 C07/C08/C09; Q05 C05 plus the earlier-expectation source S02; O-Q01 O-C02 plus measurements O-M01:1 and O-M01:3; O-Q12 O-C23 plus all three O-M07 measurements; O-Q13 O-C26 plus all four O-M11 measurements; O-Q14 is `unknown` with context O-C25, O-C07. Cases with no claim IDs (Q07, Q10, Q12, O-Q08) are `unknown` with `context_claims` where useful. Prohibited assertions are the specific wrong claims the expected answer denies (for example "the entire complex stopped", "same lot", "individual 80%").
- [ ] **Step 3: Run `oracle` and read every finding against the sources;** record disagreements in `docs/evaluation-oracle-review.md` (each expected answer, what supports it, what does not, and any correction proposed). Do not edit the acceptance records; corrected oracle text lives in the eval case `notes` until the user confirms.
- [ ] **Step 4: Implement, run tests, ruff.**
- [ ] **Step 5: Checkpoint.**

### Task 5: Comparability model and display builder

**Files:** Create `backend/app/comparability/{__init__,model,display,reports}.py`; Tests `backend/tests/test_comparability_model.py`, `test_comparability_display.py`, `test_comparability_reports.py`.

**Interfaces:**
- `Report(id, entity, measure, statistic, unit_symbol, period: Period, value_text, epistemic_status, release_status, source_ids, origin_groups, scope: dict[str, str | None])` where `Period(kind, start, end_exclusive, at)` and `scope` carries the metadata the packs do not yet hold: `geography`, `population`, `methodology`, `seasonal_adjustment` (all `None` today).
- `comparison_key(report) -> tuple | None`: `(entity, measure, statistic, unit_symbol, period)` or `None` if any element is missing. `is_forecast(report)`.
- `candidate_groups(reports) -> list[list[Report]]`: groups with equal key, same lane (forecast or not), and at least two distinct origin groups.
- `Membership(report_id, assessment: Literal["comparable","not_comparable","unresolved"], reason, reviewer)`; `Relation(left, right, relation: Literal["contradicts","revises","duplicates_origin","different_scope","supports"], rationale, reviewer)`.
- `build_display(reports, memberships, relations) -> ComparisonDisplay(cards, range, notes)`: `Card(report_id, label, value_text, unit_symbol, period_label, source_ids, lane, revised_from, difference)`; `Range(low, high, n, label)` with label exactly `"range of N reports; not a confidence interval"`.
  Rules: cards for every active report; a `revises` relation hides the superseded report from counts and adds `revised_from` to the current card; a `duplicates_origin` relation or shared origin group counts once; a range appears only when at least two active, independent, reviewer-assessed `comparable` reports share the same lane and unit, computed with `Decimal` over original value text; a `not_comparable` or `different_scope` member produces a card `difference` and no range; one report gives one card and no range or band; forecast and reported never share a range.
- `build_reports(measurements, investigations, vocabulary) -> list[Report]`: units from the vocabulary measure, source IDs and origin groups from the pack metric group (documented as group-level, not point-level).

- [ ] **Step 1: Failing tests** (all Synthetic test data): matching key with two origins is a candidate group; same origin twice is not; a missing period makes the key `None`; forecast and reported never group; range appears for two comparable independent reports and shows `Decimal` min and max with the exact label; no range when either is `unresolved`, when origins are shared, when a revision is the only other member, or when lanes differ; `revises` hides the old report and sets `revised_from`; single report yields one card and `range is None`; a real-corpus test asserts `candidate_groups(build_reports(<the 37 real measurements>))` is empty (the packs contain no conflict set, as recommendation 03 says).
- [ ] **Step 2 to 4:** red, implement, green, lint, boundary rule entries.
- [ ] **Step 5: Checkpoint.**

### Task 6: Storage, migration 009 and read endpoints

**Files:** Create `backend/app/storage/migrations/009_comparability.sql`, `backend/app/storage/comparisons.py`; Modify `backend/app/main.py`; Tests `backend/tests/test_comparability_postgres.py`, `test_comparability_api.py`.

**Schema:** `comparison_set(id text PK, definition_version text, comparison_key jsonb, created_at)`; `comparison_membership(id uuid PK, set_id text FK, report_id text, assessment text CHECK, reason text non-blank, reviewer text non-blank, recorded_at, supersedes_id uuid FK NULL)`; `claim_relation(id uuid PK, left_ref text, right_ref text, relation text CHECK, rationale text non-blank, evidence_refs jsonb, reviewer text non-blank, recorded_at)`; all with the existing `prevent_history_rewrite()` trigger. A unique partial index enforces a single current membership per `(set_id, report_id)`: a later row must name the row it supersedes.

**Interfaces:** `PostgresComparisons(database, normalisation)` with `create_set(set_id, definition_version, key: dict)`, `assess(set_id, report_id, assessment, reason, reviewer, supersedes: UUID | None = None) -> UUID`, `relate(left_ref, right_ref, relation, rationale, reviewer, evidence_refs=()) -> UUID`, `displays(investigations, vocabulary) -> list[tuple[str, ComparisonDisplay]]`. `assess` validates that `report_id` is a measurement in the accepted release (else `KeyError`) and raises `ReviewConflict` for a second current membership without `supersedes`.

- [ ] **Step 1: Failing tests:** each new table is append-only; a blank reviewer or reason is refused; a duplicate current membership without `supersedes` conflicts; superseding works and only the latest counts; an unknown report ID is refused; recorded history tables' hashes are unchanged after any comparability write; the API returns `[]` with no sets, one display with cards after synthetic sets are created on real measurements (Synthetic test data: two real measurements assigned to a set purely to exercise the code path, in a disposable schema), 404 for an unknown set, 503 when unconfigured.
- [ ] **Step 2 to 4:** red, implement, green; regenerate `contracts/openapi.json` and `apps/web/src/generated/api.ts`; `npx tsc --noEmit`; full suite; ruff.
- [ ] **Step 5: Checkpoint.**

### Task 7: Rehearsal, evaluation run and documentation

- [ ] **Step 1:** Full backend suite, ruff, `format:check`, licence gate, `normalise.py check`, browser workflows.
- [ ] **Step 2:** `scripts/evaluate.py run` and `oracle`; paste the raw results into `docs/evaluation-oracle-review.md`.
- [ ] **Step 3: Rehearse migration 009** on a restored scratch copy of a fresh backup (`nexus_rehearsal_m3`): apply, create a synthetic set, record an assessment, confirm recorded-history hashes identical. Do not print connection URLs.
- [ ] **Step 4: Docs:** `docs/roadmap.md` (M3 status), `docs/decisions.md` (proposals above), `docs/development-log.md`, `docs/development-status.md`, `README.md` (new commands), this plan's "As built".
- [ ] **Step 5: Stop and ask the user:** confirm each expected answer (the [U] gate) using `docs/evaluation-oracle-review.md`; approve the comparability rules; confirm they are the only reviewer for now. On approval, back up, migrate the real database, and mark confirmed cases `user_confirmed` in the suite.

## As built (deviations from this plan)

- `Record` in the plan is `CorpusRecord` in code, to avoid clashing with the base class `Record`.
- Corpus records also carry `source_refs`, so the oracle audit can check each required record against the sources it cites.
- The entity boost applies on its own (a question that only names an entity retrieves that entity's records); the first draft applied it only to lexical matches and a test caught it.
- The answer checker also checks abstentions for prohibited text and required qualifiers, so an unknown case (Q12) can require a stated limitation.
- Answerers receive `(question, hits)` only; the checker holds the oracle.
- `displays` returns `list[ComparisonSet]` and there is a `display(set_id)` helper.
- The plan listed negative-fixture results in `evaluate.py run`; they live in the unit tests (`test_evaluation_answers.py`) instead.
- The plan's Q12 case class `unknown` needed the abstention change above; O-Q02 and several others are `partial`, not `supported`.
- Events are not in the evaluation corpus (a limit recorded as F5).

## Self-review

- **Roadmap M3 coverage:** executable evaluations without a paid model: Tasks 1 to 4. Corrected oracles: Task 4 (`notes`, review doc). Comparability and revision-lineage with side-by-side display data: Tasks 5, 6. Exit [T] deterministic and covers all 26: Task 4 tests (26 cases; determinism test in Task 2, and `run` twice identical in Task 7). [A]: Task 4 step 3. [U]: Task 7 step 5, including who marks reports comparable.
- **Placeholders:** case contents are authored data in Task 4 (with named sources of truth); every code task lists exact signatures and the tests that pin them.
- **Type names:** `EvalCase`, `EvalSuite`, `Corpus`, `Record`, `Hit`, `RetrievalScore`, `Answer`, `Fact`, `Report`, `Membership`, `Relation`, `ComparisonDisplay`, `Card`, `Range`, `PostgresComparisons` are used consistently.
- **Known limits, stated:** the retriever is a baseline and its misses are the point of measuring; source binding of measurements is group-level (pack metric `source_ids`) until M4 adds point-level passages; no real conflict set exists, so comparability is proven on synthetic data only.
