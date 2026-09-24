# M2 Evidence Model Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline). Steps use checkbox (`- [ ]`) syntax. **The user makes every git commit; there are no commit steps. Each task ends with a checkpoint line in `docs/development-log.md` instead.**

**Goal:** Make claims, time, measurements and entities filterable and comparable through one reviewed, versioned, append-only *normalisation release*, without changing any recorded claim, proposal, decision or version.

**Architecture:** A repo-owned release document (`normalisation/releases/*.json`) holds every proposed mapping: claim vocabulary, temporal interpretation, source classes, canonical entities with legacy-ID aliases, and measurement identities. A pure validator proves it covers the real packs exactly. A hand-written migration adds append-only tables; a command records a release (idempotent), and a person records an accept/reject decision. Read endpoints serve the accepted release. Nothing here edits the 44 claims: it is a *projection* beside them (recommendation 01).

**Tech Stack:** Python 3.13 / pydantic v2 / psycopg 3 / FastAPI / PostgreSQL (existing); pytest + ruff; `openapi-typescript` for the frontend types.

## Global Constraints

- Historical claim IDs, payloads, proposals, decisions and accepted versions are never changed. `seed_immutable` is not disabled by any M2 migration. (`docs/decisions.md`, "Normalisation")
- Vocabularies are Nexus-owned and closed; external crosswalks are optional (recommendation 01).
- Unknown vocabulary codes fail validation; they never become new codes silently.
- Metric values keep their original decimal text (`"5.97"`), never a float round trip (recommendation 04).
- No unit conversion in M2: the unit registry records scale only. Cross-dimension conversion (mass to volume) is out of scope and blocked.
- Unknown validity stays `unknown`; it is never treated as "always valid" (recommendation 02).
- `epistemic_status` is never promoted by publisher class. `observed` is assigned to nothing in v1.
- The projection is *proposed* until a person records an accept decision. Data adapters (M4 onward) may read accepted releases only.
- Back up the database before any migration; rehearse on a restored scratch copy first; ask the user before touching the real database.
- Code style: cohesive domain modules, precise names, no speculative layers (`docs/architecture-and-development.md`). Ruff lint and format pass on files this plan touches.
- Windows: run Python with `PYTHONIOENCODING=utf-8`; use `git grep`, not repo-wide grep (`.venv`).

## Decisions this plan takes (assistant proposals, for the user to approve at the gate)

1. **One release covers both investigations.** Simpler than per-case releases, and canonical entity IDs need one namespace. A later release must keep every earlier canonical ID and alias (checked).
2. **Approval is a stored decision on the release**, not a per-row state, so all rows stay immutable.
3. **Canonical entity ID = `<category>/<slug>`** (for example `place/china`, `material/crude-oil`), using the two-level taxonomy in `docs/frontend-rebuild.md`. Legacy IDs (`oil-china`, `smelter`) resolve as aliases scoped by `case_id`.
4. **Measurement IDs are permanent and readable**: `<case_id>:<metric_id>:<n>` where `n` is the point's position in the *reviewed* release. The position is a provenance pointer only (recommendation 04).
5. **`period` overloading is repaired in the projection, not in the pack**: O-M06 and O-M11 rows get an `entity` (canonical ID) and a period taken from the group's context; the pack's `period` text is kept as `original_label`.
6. **Old and replacement sources both get classes.** O-S21 to O-S27 copy the class of the source they replace.

## File Structure

| Path | Responsibility |
|---|---|
| `normalisation/vocabulary-v1.json` (create) | The closed vocabularies and the unit/measure registry, version `1`. |
| `normalisation/releases/2026-09-24.json` (create) | The proposed release: entities+aliases, claim projections, source classes, measurements. |
| `backend/app/normalisation/__init__.py` (create) | Empty package marker. |
| `backend/app/normalisation/vocabulary.py` (create) | `Vocabulary` model, `load_vocabulary(path)`, code membership checks. |
| `backend/app/normalisation/release.py` (create) | `Release` models and `validate_release(...)`: the pure coverage and consistency rules. |
| `backend/app/normalisation/measurements.py` (create) | `read_metric_points(pack_path)`: original decimal text for every metric point. |
| `backend/app/storage/migrations/008_normalisation.sql` (create) | Append-only tables and triggers. |
| `backend/app/storage/normalisation.py` (create) | `PostgresNormalisation`: record, decide, read. |
| `backend/app/main.py` (modify) | Three read endpoints and wiring. |
| `scripts/normalise.py` (create) | `check`, `record`, `decide` commands. |
| `scripts/render_normalisation_review.py` (create) | Renders the release as a human review sheet. |
| `docs/normalisation-review.md` (create, generated) | The [U] artifact: 44-claim table, entities, decisions to make, [A] arguments. |
| `backend/tests/test_normalisation_vocabulary.py`, `test_normalisation_release.py`, `test_normalisation_data.py`, `test_normalisation_postgres.py` (create) | One test module per layer. |
| `contracts/openapi.json`, `apps/web/src/generated/api.ts` (regenerate) | Contract and types. |

Existing helper to reuse: `app.storage.reviews.fingerprint(value)` (sha256 of sorted JSON) and `Database.connect()`.

---

### Task 1: Vocabulary registry and loader

**Files:**
- Create: `normalisation/vocabulary-v1.json`, `backend/app/normalisation/__init__.py`, `backend/app/normalisation/vocabulary.py`
- Test: `backend/tests/test_normalisation_vocabulary.py`

**Interfaces:**
- Produces: `Vocabulary` (frozen pydantic model) with fields `version: str`, `predicates: dict[str, Predicate]`, `epistemic_statuses: list[str]`, `content_types: list[str]`, `modalities: list[str]`, `publisher_classes: list[str]`, `document_classes: list[str]`, `release_statuses: list[str]`, `units: dict[str, Unit]`, `measures: dict[str, Measure]`, `statistics: list[str]`, `precisions: list[str]`, `valid_kinds: list[str]`, `entity_categories: dict[str, list[str]]` (category to allowed subtypes).
  `Predicate(definition: str)`; `Unit(symbol: str, dimension: str, scale: str)` where `scale` is a decimal string like `"1000000"`; `Measure(name: str, unit: str, statistic: str, material_basis: str)`.
  `load_vocabulary(path: Path) -> Vocabulary`; `Vocabulary.content_hash() -> str`.

- [ ] **Step 1: Write the failing test**

```python
"""The vocabulary is closed: every code used anywhere must exist in a versioned file."""

from pathlib import Path

import pytest

from app.normalisation.vocabulary import Vocabulary, load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "normalisation" / "vocabulary-v1.json"


@pytest.fixture(scope="module")
def vocabulary() -> Vocabulary:
    return load_vocabulary(V1)


def test_version_and_status_lists_match_recommendation_01(vocabulary):
    assert vocabulary.version == "1"
    assert vocabulary.epistemic_statuses == [
        "observed", "reported", "estimated", "inferred", "forecast", "scenario", "unknown",
    ]
    assert vocabulary.modalities == [
        "actual", "planned", "capability", "generic", "required", "unknown",
    ]
    assert "wire_rod_contract_with" not in vocabulary.predicates  # material lives in a qualifier


def test_every_predicate_is_defined(vocabulary):
    assert len(vocabulary.predicates) == 26  # distinct new predicates in the 44-row table
    assert all(p.definition.strip() for p in vocabulary.predicates.values())


def test_million_is_a_scale_and_percent_is_a_fraction(vocabulary):
    assert vocabulary.units["million_barrel_petroleum_per_day"].scale == "1000000"
    assert vocabulary.units["percent"].scale == "0.01"


def test_content_hash_is_stable_and_changes_with_content(vocabulary):
    assert vocabulary.content_hash() == vocabulary.content_hash()
    changed = vocabulary.model_copy(update={"version": "2"})
    assert changed.content_hash() != vocabulary.content_hash()


def test_a_duplicate_code_is_rejected(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(
        '{"version":"1","predicates":{},"epistemic_statuses":["a","a"],"content_types":[],'
        '"modalities":[],"publisher_classes":[],"document_classes":[],"release_statuses":[],'
        '"units":{},"measures":{},"statistics":[],"precisions":[],"valid_kinds":[],'
        '"entity_categories":{}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_vocabulary(bad)
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `cd backend; ..\.venv\Scripts\python -m pytest tests/test_normalisation_vocabulary.py -q`
Expected: FAIL (`ModuleNotFoundError: app.normalisation`).

- [ ] **Step 3: Implement `vocabulary.py`**

```python
"""Closed, versioned Nexus vocabularies. A code that is not listed here does not exist."""

import json
from pathlib import Path

from pydantic import model_validator

from app.knowledge import Record
from app.storage.reviews import fingerprint


class Predicate(Record):
    definition: str


class Unit(Record):
    symbol: str
    dimension: str
    scale: str  # exact decimal text; "million" is 1000000, "percent" is 0.01


class Measure(Record):
    name: str
    unit: str
    statistic: str
    material_basis: str


class Vocabulary(Record):
    version: str
    predicates: dict[str, Predicate]
    epistemic_statuses: list[str]
    content_types: list[str]
    modalities: list[str]
    publisher_classes: list[str]
    document_classes: list[str]
    release_statuses: list[str]
    units: dict[str, Unit]
    measures: dict[str, Measure]
    statistics: list[str]
    precisions: list[str]
    valid_kinds: list[str]
    entity_categories: dict[str, list[str]]

    @model_validator(mode="after")
    def codes_are_unique_and_measures_use_known_units(self) -> "Vocabulary":
        for name in (
            "epistemic_statuses", "content_types", "modalities", "publisher_classes",
            "document_classes", "release_statuses", "statistics", "precisions", "valid_kinds",
        ):
            codes = getattr(self, name)
            if len(codes) != len(set(codes)):
                raise ValueError(f"duplicate code in {name}")
        for code, measure in self.measures.items():
            if measure.unit not in self.units:
                raise ValueError(f"measure {code} uses unknown unit {measure.unit}")
            if measure.statistic not in self.statistics:
                raise ValueError(f"measure {code} uses unknown statistic {measure.statistic}")
        return self

    def content_hash(self) -> str:
        return fingerprint(self.model_dump(mode="json"))


def load_vocabulary(path: Path) -> Vocabulary:
    return Vocabulary.model_validate_json(path.read_text("utf-8"))
```

- [ ] **Step 4: Author `normalisation/vocabulary-v1.json`**

Content rules (all from `docs/recommendations/01-vocabularies.md`, `02-time-model.md`, `04-units-and-conversions.md`):
- `predicates`: exactly the distinct *new* predicates in the recommendation 01 "All 44 claim mappings" table (the "New predicate" column), each with a one-sentence definition. Do not add predicates that no claim uses.
- `epistemic_statuses`, `modalities`: the lists asserted in the test, in that order.
- `content_types`: the 17 in recommendation 01.
- `publisher_classes`: `company, government_agency, intergovernmental_body, research_body, news_publisher, industry_association, other, unknown`. `document_classes`: `participant_announcement, statistical_release, analysis, outlook, filing, product_reference, operations_profile, provider_update, other, unknown`. `release_statuses`: `provisional, final, revised, unspecified`.
- `statistics`: `snapshot, total, mean_rate, ratio, capacity, qualitative`. `precisions`: `day, week, month, quarter, half_year, year, fiscal_year, unknown`. `valid_kinds`: `instant, interval, unknown`.
- `units`: `barrel_petroleum` (dimension `volume`, scale `1`), `barrel_petroleum_per_day`, `barrel_petroleum_per_calendar_day`, `million_barrel_petroleum`, `million_barrel_petroleum_per_day` (scale `1000000`), `million_barrel_petroleum_per_calendar_day`, `million_tonne_metric` (dimension `mass`, scale `1000000`), `percent` (dimension `ratio`, scale `0.01`).
- `measures`: one per row of the recommendation 04 table (O-M01/02 chokepoint transit rate; O-M03 world supply rate; O-M04 crude import rate; crude production rate; crude+product export rate; forecast crude production rate; route transit rate; commercial crude stocks excluding SPR; operable distillation capacity; refinery utilization; India crude imports total; country crude production rate). Names are proposed internal codes, not standard identifiers.
- `entity_categories`: the seven categories from `docs/frontend-rebuild.md` (`place, facility, infrastructure, transport_corridor, organization, material, industry`) with subtypes: every distinct pack `type` maps to exactly one (category, subtype) pair, see Task 3.

- [ ] **Step 5: Run the tests, confirm they pass, then lint**

Run: `cd backend; ..\.venv\Scripts\python -m pytest tests/test_normalisation_vocabulary.py -q; cd ..; .venv\Scripts\python -m ruff check backend/app/normalisation backend/tests/test_normalisation_vocabulary.py; .venv\Scripts\python -m ruff format backend/app/normalisation backend/tests/test_normalisation_vocabulary.py`
Expected: 5 passed; ruff clean.

- [ ] **Step 6: Checkpoint**: add a "M2 task 1 done" line to `docs/development-log.md` with the vocabulary hash printed by `python -c "from app.normalisation.vocabulary import *; print(load_vocabulary(...).content_hash())"`.

---

### Task 2: Release model and the pure validator

**Files:**
- Create: `backend/app/normalisation/release.py`
- Test: `backend/tests/test_normalisation_release.py`

**Interfaces:**
- Consumes: `Vocabulary` (Task 1); `Investigation` (`app.investigation`).
- Produces (all frozen `Record` subclasses):
  `Alias(case_id: str, legacy_id: str)`
  `EntityRecord(canonical_id: str, name: str, category: str, subtype: str, aliases: list[Alias])`
  `Temporal(valid_kind: str, valid_start: date | None, valid_end_exclusive: date | None, valid_at: date | None, precision: str, original_label: str | None, statistic: str, state: str)` where `state` is `legacy_bounds | unknown | proposed_reinterpretation`
  `ClaimRecord(case_id: str, claim_id: str, predicate: str, epistemic_status: str, content_type: str, modality: str, release_status: str, qualifiers: dict[str, str], temporal: Temporal, needs_semantic_review: bool, note: str | None)`
  `SourceRecord(case_id: str, source_id: str, publisher_class: str, document_class: str, legacy_reported_method: str | None)`
  `MeasurementRecord(id: str, case_id: str, metric_id: str, point_index: int, measure: str, value_text: str, entity: str | None, original_label: str, temporal: Temporal, epistemic_status: str, release_status: str, claim_ids: list[str])`
  `Release(release_id: str, vocabulary_version: str, entities, claims, sources, measurements)`
  `validate_release(release: Release, vocabulary: Vocabulary, investigations: list[Investigation], metric_texts: dict[tuple[str, str], list[str]]) -> list[str]` returning problem descriptions (empty means valid). `metric_texts[(case_id, metric_id)]` is the list of original value texts.
  `content_hash(release) -> str`.

Rules `validate_release` enforces (each is one test): every real claim appears exactly once and none extra; every real source exactly once; every real entity id is an alias of exactly one canonical entity, and no alias appears twice; every metric point appears exactly once as a measurement with the same value text; every code is in the vocabulary (predicate, statuses, classes, measure, unit via measure, category/subtype, precision, valid kind); `observed` is never used; `estimated`/`forecast` are only allowed with a stated reason in `note`; an `interval` has start and exclusive end with start < end; an `instant` has `valid_at` and no interval; `unknown` has neither; a claim's `temporal.state == legacy_bounds` must match the claim's stored `valid_from`/`valid_to` (`valid_end_exclusive == valid_to + 1 day`) and `unknown` must match two null dates; `proposed_reinterpretation` requires `note`.

- [ ] **Step 1: Write failing tests** using two tiny synthetic investigations built in the test (marked "Synthetic test data") and a tiny vocabulary loaded from a dict. One test per rule above, each asserting the specific problem text, for example:

```python
def test_a_claim_missing_from_the_release_is_reported(make):
    investigations, vocabulary, release = make()
    release = release.model_copy(update={"claims": release.claims[:-1]})
    problems = validate_release(release, vocabulary, investigations, {})
    assert any("missing claim" in p and "C2" in p for p in problems)


def test_an_extra_claim_is_reported(make):
    ...
    assert any("unknown claim" in p and "C9" in p for p in problems)


def test_observed_is_never_assigned(make):
    ...
    assert any("observed" in p for p in problems)


def test_legacy_bounds_must_match_the_stored_dates(make):
    ...  # claim C1 stored 2026-04-01..2026-06-30, release says end_exclusive 2026-06-30
    assert any("C1" in p and "legacy bounds" in p for p in problems)


def test_the_same_alias_cannot_point_at_two_entities(make):
    ...
    assert any("alias" in p and "twice" in p for p in problems)
```

The `make` fixture builds the minimal valid trio and each test perturbs one thing; a first test asserts the unperturbed trio yields `[]`.

- [ ] **Step 2: Run, confirm failure** (`ImportError: release`).
- [ ] **Step 3: Implement** `release.py`: models as specified plus `validate_release`, written as small named checks (`_claim_coverage`, `_source_coverage`, `_entity_coverage`, `_measurement_coverage`, `_codes`, `_temporal`) each returning `list[str]`; `validate_release` concatenates them in that order. `content_hash` is `fingerprint(release.model_dump(mode="json"))`.
- [ ] **Step 4: Run, confirm pass; ruff.**
- [ ] **Step 5: Checkpoint** line in the development log.

---

### Task 3: Original metric text and the release data (the mapping)

**Files:**
- Create: `backend/app/normalisation/measurements.py`, `normalisation/releases/2026-09-24.json`
- Test: `backend/tests/test_normalisation_data.py`

**Interfaces:**
- Produces: `read_metric_points(pack_path: Path) -> dict[str, list[str]]` mapping each metric ID to the original decimal text of each point value, in point order. It parses with `json.loads(text, parse_float=str, parse_int=str)` so `5.97` stays `"5.97"` and `13.7` never becomes `13.699999...`.

- [ ] **Step 1: Failing tests for `read_metric_points`**

```python
def test_original_decimal_text_is_preserved(tmp_path):
    pack = tmp_path / "evidence-pack.json"
    pack.write_text('{"briefing":{"metrics":[{"id":"M","points":[{"value":5.97},{"value":13.7},{"value":100.0}]}]}}')
    assert read_metric_points(pack) == {"M": ["5.97", "13.7", "100.0"]}
```

- [ ] **Step 2: Implement** `measurements.py`; run; pass.

- [ ] **Step 3: Failing data tests** in `test_normalisation_data.py` that run `validate_release` against the *real* packs, vocabulary and release file (skipped until the file exists):

```python
def test_the_release_covers_every_real_record_exactly(problems):
    assert problems == []

def test_there_are_44_claims_and_41_sources_and_43_entities_and_37_points(release):
    assert (len(release.claims), len(release.sources), len(release.entities), len(release.measurements)) == (44, 41, 43, 37)
```

(43 entities are the pack entities; each canonical entity in this first release maps one legacy ID, since the two packs share none.)

```python
@pytest.mark.parametrize("claim_id", ["O-C07", "O-C08", "O-C12", "O-C13", "C11", "C13"])
def test_the_known_semantic_mismatches_are_flagged_for_review(release, claim_id):
    claim = next(c for c in release.claims if c.claim_id == claim_id)
    assert claim.needs_semantic_review and claim.note

def test_no_claim_is_observed_and_ground_truth_is_untouched(release, investigations):
    assert all(c.epistemic_status != "observed" for c in release.claims)

def test_the_thirteen_bounded_claims_keep_their_legacy_dates(release):
    bounded = [c for c in release.claims if c.temporal.state != "unknown"]
    assert len(bounded) == 13
```

Note the mismatch test asserts the flag, not that the mapping is right: the [A] arguments live in Task 6.

- [ ] **Step 4: Author the release JSON.** Sources of truth, all in the repo:
  - **Claims (44):** the "All 44 claim mappings" table in `docs/recommendations/01-vocabularies.md`. Columns map to `predicate`, `epistemic_status`, `content_type`, `modality` and `qualifiers` (split the "Modality / retained qualifier" cell at the first `;`: text before is the modality, the rest become qualifier entries such as `material: anodes`, `shipment_scope: unresolved`). `release_status` is `unspecified` everywhere except O-C25 (`provisional`) and O-C24/O-C08 (`unspecified`). `needs_semantic_review` is true for O-C07, O-C08, O-C12, O-C13, C11, C13 and O-C25; `note` states the mismatch in one sentence taken from the recommendation.
  - **Temporal:** the 31 unbounded claims are `valid_kind: unknown`, `state: unknown`. The 13 bounded claims use `state: legacy_bounds` with `valid_end_exclusive = valid_to + 1 day` and `precision` from `source_as_of` (`2026-Q2` quarter, `2026-06` month, `2026-H1` half_year, `2025-H1` half_year, `2026-04` month, `2026-08` month, `2026-27 (Apr-Aug, provisional)` fiscal_year), with two exceptions recorded as `proposed_reinterpretation` and a `note`: **O-C23** becomes `instant` at 2026-09-11 (statement and metric are a snapshot; stored range 2026-09-05 to 2026-09-11), and **O-C24** becomes `instant` at 2026-01-01 (equal bounds mean a capacity snapshot). **O-C13** keeps its October interval and gets `note: policy applies to October; decided in September; not observed output`.
  - **Sources (41):** the "Source migration mapping" table in recommendation 01; O-S21 to O-S27 copy the class of O-S01, O-S11, O-S20, O-S05, O-S07, O-S08, O-S10 respectively (matching the `Replacement version of` note). `legacy_reported_method` is `web_tool` for every source whose `review_status` ends in `_read_via_web`; otherwise `null`. Note that seven oil sources now have a review status beginning `excerpt_verified_verbatim_against_fetched_page_text`; their `legacy_reported_method` is `null`.
  - **Entities (43):** canonical ID `<category>/<slug>`; mapping from pack `type` to (category, subtype): `country to place/country`, `maritime_chokepoint to place/maritime_chokepoint`, `maritime_route to place/maritime_route`, `production_region to place/production_region`, `facility to facility/<see below>`, `facility_group to facility/facility_group`, `site_complex to facility/site_complex`, `infrastructure to infrastructure/pipeline` for the three pipelines and `infrastructure/rail_line` for `rail`, `transport_corridor to transport_corridor/canal_corridor`, `organization to organization/company`, `producer_group to organization/producer_group`, `material to material/<slug>`, `product_category to material/product_category`, `industry to industry/oil_refining`, `system to industry/industry_system`. Per-entity `facility` subtypes (smelter, export_terminal, mine, dry_port, port) are chosen by reading each entity's name. Names: the pack names, except the **user-decision** names in Task 7.
  - **Measurements (37):** one per point of the 11 metric groups. Measure codes per the recommendation 04 table. `entity` links: O-M01 to `place/strait-of-hormuz`, O-M02 to `place/bab-el-mandeb`, O-M03 to `industry/global-oil-system`, O-M04 and O-M05 to `place/china` and `place/united-states` respectively, O-M06 per point (Malacca, Hormuz, Cape of Good Hope, Suez + SUMED, Bab el-Mandeb), O-M07 to O-M09 to `place/united-states`, O-M10 to `place/india`, O-M11 per point (Saudi Arabia, Iraq, Russia, Iran). **Russia and Iran are not entities in the pack**: create them in the registry with no aliases only if the user approves; otherwise leave `entity: null` and keep the label. This is a Task 7 decision; the first draft leaves them null.
    `claim_ids` links only where the recommendation supports it (for example O-M01 to O-C02, O-M02 to O-C03, O-M11 Iraq point to O-C26, O-M07 to O-C23, O-M08 to O-C24, O-M10 to O-C25). Everything else is an empty list. Temporal for a measurement comes from its point period (`2026-Q2`), or from the group's stated context for O-M06 (`2025-H1`) and O-M11 (`2026-08`). `week ending 2026-09-11` is `interval` with `precision: week`; a bare date is `instant`.
    `epistemic_status` follows the point's `status`; `forecast` requires a `note` naming the issuer.
- [ ] **Step 5: Run the data tests; fix the JSON until they pass** (`validate_release` messages point at the exact record).
- [ ] **Step 6: Checkpoint** line in the development log.

---

### Task 4: Migration 008 and storage

**Files:**
- Create: `backend/app/storage/migrations/008_normalisation.sql`, `backend/app/storage/normalisation.py`
- Test: `backend/tests/test_normalisation_postgres.py`

**Schema** (all tables append-only using the existing `prevent_history_rewrite()` trigger, no `seed_immutable` change):

```sql
CREATE TABLE vocabulary_release (
    version text PRIMARY KEY,
    content_hash text NOT NULL,
    definition jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE normalisation_release (
    id text PRIMARY KEY,
    vocabulary_version text NOT NULL REFERENCES vocabulary_release(version),
    content_hash text NOT NULL UNIQUE,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE normalisation_decision (
    release_id text PRIMARY KEY REFERENCES normalisation_release(id),
    decision text NOT NULL CHECK (decision IN ('accept', 'reject')),
    reviewer text NOT NULL CHECK (length(trim(reviewer)) > 0),
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE entity_registry (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    canonical_id text NOT NULL, name text NOT NULL, category text NOT NULL, subtype text NOT NULL,
    PRIMARY KEY (release_id, canonical_id)
);
CREATE TABLE entity_alias (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    case_id text NOT NULL, legacy_id text NOT NULL, canonical_id text NOT NULL,
    PRIMARY KEY (release_id, case_id, legacy_id)
);
CREATE TABLE claim_projection (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    claim_id text NOT NULL REFERENCES knowledge_assertions(id),
    basis_proposal_id uuid NOT NULL REFERENCES knowledge_proposals(id),
    predicate text NOT NULL, epistemic_status text NOT NULL, content_type text NOT NULL,
    modality text NOT NULL, release_status text NOT NULL, qualifiers jsonb NOT NULL,
    valid_kind text NOT NULL, valid_start date, valid_end_exclusive date, valid_at date,
    precision text NOT NULL, original_label text, statistic text NOT NULL, time_state text NOT NULL,
    needs_semantic_review boolean NOT NULL, note text,
    PRIMARY KEY (release_id, claim_id)
);
CREATE TABLE source_classification (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    source_id text NOT NULL REFERENCES evidence_sources(id),
    publisher_class text NOT NULL, document_class text NOT NULL, legacy_reported_method text,
    PRIMARY KEY (release_id, source_id)
);
CREATE TABLE measurement (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    id text NOT NULL, case_id text NOT NULL, metric_id text NOT NULL, point_index integer NOT NULL,
    measure text NOT NULL, value_text text NOT NULL, entity text, original_label text NOT NULL,
    valid_kind text NOT NULL, valid_start date, valid_end_exclusive date, valid_at date,
    precision text NOT NULL, epistemic_status text NOT NULL, release_status text NOT NULL,
    claim_ids text[] NOT NULL, note text,
    PRIMARY KEY (release_id, id)
);
```
followed by one `CREATE TRIGGER <table>_immutable BEFORE UPDATE OR DELETE ... EXECUTE FUNCTION prevent_history_rewrite();` per table. `basis_proposal_id` is the claim's earliest (import) proposal, resolved at record time.

**Interfaces:**
- Produces `PostgresNormalisation(database)` with:
  `record_release(release: Release, vocabulary: Vocabulary) -> str` (returns the release ID; idempotent when the same content hash is recorded again; raises `ReviewConflict` if the ID exists with different content; refuses a release that drops any canonical ID or alias present in the latest **accepted** release);
  `decide(release_id: str, decision: Literal["accept","reject"], reviewer: str, reason: str) -> None` (one decision per release; a second, different decision raises `ReviewConflict`);
  `accepted_release_id() -> str | None` (the latest accepted);
  `claim_projection(claim_id) -> ClaimProjection | None`, `resolve_alias(case_id, legacy_id) -> EntityRecord | None`, `measurements(entity: str | None = None) -> list[MeasurementRecord]`, each reading the accepted release only.

- [ ] **Step 1: Failing tests** (real PostgreSQL, disposable schema like `test_review_postgres.py::store`; reuse its fixture pattern in a new fixture, initialising both investigations). Tests:
  1. `record_release` stores rows and is idempotent (second call same ID, row counts unchanged).
  2. Recording changes nothing in history: fingerprint of `knowledge_proposals`, `knowledge_decisions`, `knowledge_versions`, `knowledge_assertions`, `evidence_sources`, `investigation_seed` rows before and after are identical.
  3. Nothing is readable until accepted: `claim_projection("O-C02")` is `None` after record, present after accept; rejected releases stay unreadable.
  4. `resolve_alias("oil-system-2025q3-2026q2", "oil-china")` returns `place/china`; every legacy ID of both packs resolves.
  5. UPDATE and DELETE on each new table raise the append-only error.
  6. A second decision on the same release raises `ReviewConflict`.
  7. A release that omits a previously accepted alias is refused.
  8. Migration on a database that already has migrations 001 to 007 applies 008 with row counts of old tables unchanged (use `database.migrate()` twice and compare counts).
- [ ] **Step 2: Run, confirm failure.**
- [ ] **Step 3: Write the migration and `storage/normalisation.py`.** Each write is one locked transaction (`pg_advisory_xact_lock(hashtext(schema))`) like `PostgresReviews`. `basis_proposal_id` query: `SELECT id FROM knowledge_proposals WHERE claim_id = %s ORDER BY proposed_at, id LIMIT 1`.
- [ ] **Step 4: Run, confirm pass; ruff; run the full backend suite.**
- [ ] **Step 5: Checkpoint** line in the development log.

---

### Task 5: The `normalise.py` command

**Files:**
- Create: `scripts/normalise.py`
- Test: `backend/tests/test_normalisation_command.py`

Subcommands: `check` (loads vocabulary, release and real investigations; runs `validate_release`; prints problems; exit 1 on any; no database needed), `record` (requires the database; runs `check` first; `--dry-run` prints what would be written; records vocabulary release then normalisation release), `decide <release_id> accept|reject --reviewer NAME --reason TEXT` (the user runs this, or tells the assistant to, with their name).

- [ ] **Step 1: Failing tests** for `check` only (import the script as in `test_evidence_repairs.py`): passes on the real data; fails with exit 1 and a readable message when a claim is dropped (use `tmp_path` copy of the release with one claim removed).
- [ ] **Step 2: Implement; run tests; ruff.**
- [ ] **Step 3: Checkpoint** line in the development log.

---

### Task 6: Read endpoints, contract and frontend types

**Files:**
- Modify: `backend/app/main.py` (add `normalisation: PostgresNormalisation | None` next to `reviews`; build it in `lifespan` from the same `Database`)
- Test: `backend/tests/test_normalisation_api.py`

Endpoints (all `GET`, 503 when storage is unconfigured, 404 for unknown IDs, and 200 with `null`/`[]` when no release is accepted, so the UI can say "not yet normalised"):
- `/api/claims/{claim_id}/projection` returns `ClaimProjection | null`
- `/api/entities/resolve?case_id=&legacy_id=` returns `EntityRecord | null`
- `/api/measurements?entity=` returns `list[MeasurementRecord]`

- [ ] **Step 1: Failing API tests** with `TestClient(create_app(investigations, store))` and a store that has an accepted release: projection of O-C02 has `predicate == "carries_flow_within"`; resolve returns China; measurements filtered by `place/china` returns the O-M04 points; with no accepted release all three return the empty forms. Also assert the existing `/api/investigation` response is byte-identical to before (guards "claims are untouched").
- [ ] **Step 2: Implement; run.**
- [ ] **Step 3: Regenerate the contract and types.** Run: `.\.venv\Scripts\python scripts/export_openapi.py; cd apps/web; npm run generate:api; npx tsc --noEmit`. Expected: `tsc` exits 0. If the existing browser tests break, fix or report; do not weaken them.
- [ ] **Step 4: Full suite; ruff; checkpoint.**

---

### Task 7: The review sheet and [A] arguments

**Files:**
- Create: `scripts/render_normalisation_review.py`, `docs/normalisation-review.md` (generated then extended by hand below the marker `<!-- assistant analysis -->`)
- Test: `backend/tests/test_normalisation_review_sheet.py`

- [ ] **Step 1: Failing test:** the rendered sheet contains all 44 claim IDs, all 43 canonical entities, and the user-decision list; rendering is deterministic (two runs identical).
- [ ] **Step 2: Implement the renderer** (release JSON to Markdown tables: claims with old and new columns, entities with aliases, sources with classes, measurements grouped by metric).
- [ ] **Step 3: Write the [A] analysis** under the marker: for each of O-C07, O-C08, O-C12, O-C13 (and C11/C13, O-C25) quote the stored statement, caveat and cited excerpt from the pack, state the mismatch, state the mapping chosen and the alternative, and say what evidence would settle it. Read the excerpts; do not rely on the recommendation's summary. Flag any disagreement with recommendation 01.
- [ ] **Step 5: List the user decisions** at the top of the sheet: approve the vocabulary lists; canonical names for China (`China` vs `People's Republic of China`), the United States, the UAE and other countries; whether to add Russia and Iran to the registry so O-M11 links; the `O-C07` epistemic label; the two proposed reinterpretations (O-C23, O-C24); the `observed` rule.
- [ ] **Step 6: Checkpoint.**

---

### Task 8: Rehearsal, full verification and documentation

- [ ] **Step 1:** Full backend suite, ruff (my files), licence gate, `scripts/normalise.py check`, `scripts/verify_excerpts.py --pack oil` (must still pass).
- [ ] **Step 2: Rehearse the migration and recording on a scratch copy.** Backup (`scripts/backup-database.py`), restore to `nexus_rehearsal_m2` (`scripts/restore-database.py <dump> --database nexus_rehearsal_m2`), run `Database.migrate()` with `NEXUS_DATABASE_URL` pointing at it, run `scripts/normalise.py record`, then compare history hashes with the real database's: identical for `knowledge_*`, `evidence_sources`, `investigation_seed`. Do not print the connection URL.
- [ ] **Step 3: Update docs:** `docs/roadmap.md` (M2 status), `docs/decisions.md` (the six proposals above, as proposals), `docs/development-log.md`, `docs/development-status.md`, `docs/methodology.md` (the two data gaps are now addressed by a proposed release; not yet accepted), `README.md` (the new commands).
- [ ] **Step 4: Stop and ask the user** (roadmap [U] gate): review `docs/normalisation-review.md`; approve the vocabulary lists; settle canonical names; decide the listed judgement calls. Then, only on their say-so: back up, `python scripts/normalise.py record`, and the user (or the assistant on their instruction with their name) runs `python scripts/normalise.py decide <release_id> accept --reviewer <name> --reason <text>`.

## As built (deviations from this plan)

- `estimated` claims need no note; only `forecast` does (the plan's first draft required both, which would have forced a note on 15 routine claims).
- The hashing helper lives in `app/normalisation/digest.py`, not `app.storage.reviews`, because `tests/test_boundaries.py` forbids domain modules importing storage; the boundary rule now covers the normalisation modules.
- Shared test fixtures moved to `backend/tests/conftest.py`.
- Migration 008 also stores `case_id`, `temporal_label`, `statistic` and `time_state` columns, and `measurement` keeps the pack's own label separately from the temporal label.
- Task 4's "upgrade-database" test is covered by the scratch-database rehearsal on a restored real backup, not by a unit test.
- The release JSON was produced by a one-off builder that parsed the recommendation's 44-row table; the JSON is the reviewed artifact and the builder was not kept.
- Added `/api/normalisation/status`, which the plan did not list.

## Self-review

- **Spec coverage (roadmap M2 "Build"):** vocabulary projection for predicate, epistemic status, content type, source class: Tasks 1, 3. Entity registry with legacy aliases: Tasks 3, 4. Measurement identity: Tasks 3, 4. Metric-to-entity links: Task 3 (`entity`, `claim_ids`). Temporal fields: Tasks 2, 3. "Needs its own command": Task 5. "Back up before migrating": Task 8. Exit checks: [T] mapping script, no omissions/extras: Tasks 2, 3, 5; legacy IDs resolve and history unchanged: Task 4 tests 2 and 4; fresh and upgrade migrations: Task 4 test 8 plus the default fixture; OpenAPI/types: Task 6. [A] semantic mismatches: Task 7. [U]: Tasks 7, 8.
- **Placeholders:** the release JSON is authored from named tables in the repo (recommendations 01, 02, 04) with every deviation listed; it is data, not code, and its correctness is enforced by `validate_release`, not by this plan.
- **Type names:** `Release`, `ClaimRecord`, `EntityRecord`, `MeasurementRecord`, `Temporal`, `Alias`, `SourceRecord`, `PostgresNormalisation` are used consistently in Tasks 2 to 6. `ClaimProjection` in Tasks 4 and 6 is the stored form of `ClaimRecord` plus `basis_proposal_id`; define it in `storage/normalisation.py` and export it from there.
- **Known limits, stated:** accepted corrections that change a claim's valid dates are not re-projected in M2; a later release supersedes. Conversion arithmetic, conflicting-source comparability (M3) and acquisition (M4) are not started.
