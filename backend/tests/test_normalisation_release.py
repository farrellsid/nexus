"""The release validator proves a mapping covers the real records exactly. Synthetic data only."""

from datetime import date
from pathlib import Path

import pytest

from app.investigation import Investigation
from app.knowledge import Briefing, Claim, Entity, EvidencePack, MetricPoint, MetricSeries
from app.normalisation.release import (
    Alias,
    ClaimRecord,
    EntityRecord,
    MeasurementRecord,
    Release,
    SourceRecord,
    Temporal,
    content_hash,
    validate_release,
)
from app.normalisation.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
CASE = "synthetic-case"


def synthetic_investigation() -> Investigation:
    """Synthetic test data: two entities, two claims (one dated), one source, one metric."""
    source = {
        "id": "S1",
        "title": "Synthetic source",
        "publisher": "Synthetic publisher",
        "published_on": None,
        "language": "en",
        "url": "https://example.org/a",
        "locator": "p1",
        "excerpt": "synthetic excerpt",
        "format": "HTML",
        "origin_group": "g",
        "checked_on": "2026-09-01",
        "review_status": "synthetic",
        "rights": "synthetic",
        "independence": "synthetic",
    }

    def claim(claim_id, predicate, start, end):
        return Claim(
            id=claim_id,
            subject="A",
            predicate=predicate,
            object="B",
            evidence_ids=["S1"],
            kind="reported_structure",
            source_as_of=None,
            valid_from=start,
            valid_to=end,
            recorded_on=date(2026, 9, 1),
            statement="Synthetic statement",
            caveat="Synthetic caveat",
            review_status="manually_source_checked_candidate",
            ground_truth=False,
        )

    pack = EvidencePack(
        schema_version="test",
        case_id=CASE,
        checked_on=date(2026, 9, 1),
        scope="synthetic",
        verdict="synthetic",
        sources=[source],
        entities=[
            Entity(id="A", name="A", type="organization", coordinates=None, location_note=""),
            Entity(id="B", name="B", type="facility", coordinates=None, location_note=""),
        ],
        claims=[
            claim("C1", "operates", date(2026, 4, 1), date(2026, 6, 30)),
            claim("C2", "produces", None, None),
        ],
        events=[],
        briefing=Briefing(
            title="t",
            window_start=date(2026, 1, 1),
            window_end=date(2026, 6, 30),
            developments_through=date(2026, 6, 30),
            framing="f",
            metrics=[
                MetricSeries(
                    id="M1",
                    title="m",
                    unit="million barrels per day",
                    description="d",
                    source_ids=["S1"],
                    points=[
                        MetricPoint(period="2026-Q1", value=5.97, status="estimate"),
                        MetricPoint(period="2026-Q2", value=13.7, status="reported"),
                    ],
                    caveat="c",
                )
            ],
        ),
    )
    return Investigation(pack=pack, questions=[])


UNKNOWN = Temporal(
    valid_kind="unknown",
    valid_start=None,
    valid_end_exclusive=None,
    valid_at=None,
    precision="unknown",
    original_label=None,
    statistic="qualitative",
    state="unknown",
)
QUARTER = Temporal(
    valid_kind="interval",
    valid_start=date(2026, 4, 1),
    valid_end_exclusive=date(2026, 7, 1),
    valid_at=None,
    precision="quarter",
    original_label="2026-Q2",
    statistic="qualitative",
    state="legacy_bounds",
)


def claim_record(claim_id, predicate, temporal, **changes):
    return ClaimRecord(
        **{
            "case_id": CASE,
            "claim_id": claim_id,
            "predicate": predicate,
            "epistemic_status": "reported",
            "content_type": "structure",
            "modality": "actual",
            "release_status": "unspecified",
            "qualifiers": {},
            "temporal": temporal,
            "needs_semantic_review": False,
            "note": None,
            **changes,
        }
    )


def measurement(index, text, **changes):
    return MeasurementRecord(
        **{
            "id": f"{CASE}:M1:{index}",
            "case_id": CASE,
            "metric_id": "M1",
            "point_index": index,
            "measure": "chokepoint_transit_rate",
            "value_text": text,
            "entity": "facility/b",
            "original_label": f"point {index}",
            "temporal": QUARTER,
            "epistemic_status": "estimated",
            "release_status": "unspecified",
            "claim_ids": [],
            "note": None,
            **changes,
        }
    )


@pytest.fixture
def make():
    def build():
        release = Release(
            release_id="synthetic-release",
            vocabulary_version="1",
            entities=[
                EntityRecord(
                    canonical_id="organization/a",
                    name="A",
                    category="organization",
                    subtype="company",
                    aliases=[Alias(case_id=CASE, legacy_id="A")],
                ),
                EntityRecord(
                    canonical_id="facility/b",
                    name="B",
                    category="facility",
                    subtype="mine",
                    aliases=[Alias(case_id=CASE, legacy_id="B")],
                ),
            ],
            claims=[
                claim_record("C1", "operates", QUARTER),
                claim_record("C2", "produces", UNKNOWN),
            ],
            sources=[
                SourceRecord(
                    case_id=CASE,
                    source_id="S1",
                    publisher_class="company",
                    document_class="analysis",
                    legacy_reported_method=None,
                )
            ],
            measurements=[measurement(0, "5.97"), measurement(1, "13.7")],
        )
        texts = {(CASE, "M1"): ["5.97", "13.7"]}
        return (
            [synthetic_investigation()],
            load_vocabulary(ROOT / "normalisation/vocabulary-v1.json"),
            release,
            texts,
        )

    return build


def problems_of(make, **changes):
    investigations, vocabulary, release, texts = make()
    release = release.model_copy(update=changes)
    return validate_release(release, vocabulary, investigations, texts)


def test_a_correct_release_has_no_problems(make):
    assert problems_of(make) == []


def test_a_claim_missing_from_the_release_is_reported(make):
    _, _, release, _ = make()
    found = problems_of(make, claims=release.claims[:-1])
    assert any("missing claim" in p and "C2" in p for p in found)


def test_an_extra_claim_is_reported(make):
    _, _, release, _ = make()
    extra = claim_record("C9", "operates", UNKNOWN)
    found = problems_of(make, claims=[*release.claims, extra])
    assert any("unknown claim" in p and "C9" in p for p in found)


def test_a_claim_listed_twice_is_reported(make):
    _, _, release, _ = make()
    found = problems_of(make, claims=[*release.claims, release.claims[0]])
    assert any("C1" in p and "twice" in p for p in found)


def test_a_source_missing_from_the_release_is_reported(make):
    found = problems_of(make, sources=[])
    assert any("missing source" in p and "S1" in p for p in found)


def test_an_entity_without_an_alias_is_reported(make):
    _, _, release, _ = make()
    lone = release.entities[0].model_copy(update={"aliases": []})
    found = problems_of(make, entities=[lone, release.entities[1]])
    assert any("entity" in p and "A" in p and "no canonical" in p for p in found)


def test_the_same_alias_cannot_point_at_two_entities(make):
    _, _, release, _ = make()
    twin = release.entities[1].model_copy(
        update={"aliases": [Alias(case_id=CASE, legacy_id="A"), Alias(case_id=CASE, legacy_id="B")]}
    )
    found = problems_of(make, entities=[release.entities[0], twin])
    assert any("alias" in p and "twice" in p for p in found)


def test_a_missing_measurement_is_reported(make):
    _, _, release, _ = make()
    found = problems_of(make, measurements=release.measurements[:1])
    assert any("missing measurement" in p and "M1:1" in p for p in found)


def test_a_measurement_must_keep_the_original_value_text(make):
    found = problems_of(make, measurements=[measurement(0, "5.970"), measurement(1, "13.7")])
    assert any("M1:0" in p and "value text" in p for p in found)


def test_an_unknown_predicate_is_reported(make):
    found = problems_of(
        make,
        claims=[claim_record("C1", "invented", QUARTER), claim_record("C2", "produces", UNKNOWN)],
    )
    assert any("C1" in p and "predicate" in p for p in found)


def test_observed_is_never_assigned(make):
    found = problems_of(
        make,
        claims=[
            claim_record("C1", "operates", QUARTER, epistemic_status="observed"),
            claim_record("C2", "produces", UNKNOWN),
        ],
    )
    assert any("observed" in p for p in found)


def test_a_forecast_needs_a_note_naming_its_issuer(make):
    found = problems_of(
        make,
        claims=[
            claim_record("C1", "operates", QUARTER, epistemic_status="forecast"),
            claim_record("C2", "produces", UNKNOWN),
        ],
    )
    assert any("forecast" in p and "note" in p for p in found)


def test_an_entity_subtype_must_belong_to_its_category(make):
    _, _, release, _ = make()
    wrong = release.entities[0].model_copy(update={"subtype": "mine"})
    found = problems_of(make, entities=[wrong, release.entities[1]])
    assert any("subtype" in p and "organization/a" in p for p in found)


def test_legacy_bounds_must_match_the_stored_dates(make):
    off_by_one = QUARTER.model_copy(update={"valid_end_exclusive": date(2026, 6, 30)})
    found = problems_of(
        make,
        claims=[
            claim_record("C1", "operates", off_by_one),
            claim_record("C2", "produces", UNKNOWN),
        ],
    )
    assert any("C1" in p and "legacy bounds" in p for p in found)


def test_stored_dates_cannot_be_projected_as_unknown(make):
    found = problems_of(
        make,
        claims=[claim_record("C1", "operates", UNKNOWN), claim_record("C2", "produces", UNKNOWN)],
    )
    assert any("C1" in p and "stored dates" in p for p in found)


def test_a_reinterpretation_needs_a_note(make):
    snapshot = Temporal(
        valid_kind="instant",
        valid_start=None,
        valid_end_exclusive=None,
        valid_at=date(2026, 6, 30),
        precision="day",
        original_label=None,
        statistic="snapshot",
        state="proposed_reinterpretation",
    )
    found = problems_of(
        make,
        claims=[claim_record("C1", "operates", snapshot), claim_record("C2", "produces", UNKNOWN)],
    )
    assert any("C1" in p and "reinterpretation" in p for p in found)


def test_an_interval_must_run_forward(make):
    backwards = QUARTER.model_copy(update={"valid_end_exclusive": date(2026, 4, 1)})
    found = problems_of(
        make, measurements=[measurement(0, "5.97", temporal=backwards), measurement(1, "13.7")]
    )
    assert any("M1:0" in p and "interval" in p for p in found)


def test_an_instant_carries_only_valid_at(make):
    bad = QUARTER.model_copy(update={"valid_kind": "instant"})
    found = problems_of(
        make, measurements=[measurement(0, "5.97", temporal=bad), measurement(1, "13.7")]
    )
    assert any("M1:0" in p and "instant" in p for p in found)


def test_content_hash_changes_with_content(make):
    _, _, release, _ = make()
    other = release.model_copy(update={"release_id": "other"})
    assert content_hash(release) == content_hash(release)
    assert content_hash(release) != content_hash(other)
