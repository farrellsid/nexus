"""Real PostgreSQL tests for normalisation releases; each test gets a disposable schema."""

from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from app.investigation import load_investigations
from app.main import INVESTIGATIONS
from app.review import ReviewConflict

ROOT = Path(__file__).resolve().parents[2]
OIL = "oil-system-2025q3-2026q2"
COPPER = "kamoa-to-cables"
HISTORY_TABLES = [
    "investigation_seed",
    "evidence_sources",
    "knowledge_assertions",
    "knowledge_proposals",
    "knowledge_proposal_evidence",
    "knowledge_decisions",
    "knowledge_versions",
]
NEW_TABLES = [
    "vocabulary_release",
    "normalisation_release",
    "normalisation_decision",
    "entity_registry",
    "entity_alias",
    "claim_projection",
    "source_classification",
    "measurement",
    "measurement_source",
]


def table_digest(database, table):
    with database.connect() as connection:
        row = connection.execute(
            sql.SQL(
                "SELECT count(*) AS n,"
                " md5(coalesce(string_agg(t::text, '' ORDER BY t::text), '')) AS d FROM {} t"
            ).format(sql.Identifier(table))
        ).fetchone()
    return row["n"], row["d"]


def accept(store, release_id):
    store.decide(release_id, "accept", "Synthetic test reviewer", "Test acceptance only")


def test_recording_is_idempotent(store, database, release, vocabulary):
    first = store.record_release(release, vocabulary)
    before = {t: table_digest(database, t) for t in NEW_TABLES}
    assert store.record_release(release, vocabulary) == first
    assert {t: table_digest(database, t) for t in NEW_TABLES} == before
    assert before["claim_projection"][0] == 44
    assert before["measurement"][0] == 37


def test_recording_changes_no_recorded_history(store, database, release, vocabulary):
    before = {t: table_digest(database, t) for t in HISTORY_TABLES}
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    assert {t: table_digest(database, t) for t in HISTORY_TABLES} == before


def test_nothing_is_readable_until_the_release_is_accepted(store, release, vocabulary):
    store.record_release(release, vocabulary)
    assert store.accepted_release_id() is None
    assert store.claim_projection("O-C02") is None
    assert store.resolve_alias(OIL, "oil-china") is None
    assert store.measurements() == []
    accept(store, release.release_id)
    assert store.accepted_release_id() == release.release_id
    projection = store.claim_projection("O-C02")
    assert projection.claim.predicate == "carries_flow_within"
    assert projection.release_id == release.release_id


def test_a_rejected_release_stays_unreadable(store, release, vocabulary):
    store.record_release(release, vocabulary)
    store.decide(release.release_id, "reject", "Synthetic test reviewer", "Test rejection only")
    assert store.accepted_release_id() is None
    assert store.claim_projection("O-C02") is None


def test_the_projection_is_based_on_the_import_proposal(store, database, release, vocabulary):
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    with database.connect() as connection:
        expected = connection.execute(
            "SELECT id FROM knowledge_proposals WHERE claim_id = 'O-C02'"
            " ORDER BY proposed_at, id LIMIT 1"
        ).fetchone()["id"]
    assert store.claim_projection("O-C02").basis_proposal_id == expected


def test_every_legacy_id_of_both_packs_resolves(store, release, vocabulary):
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    china = store.resolve_alias(OIL, "oil-china")
    assert china.canonical_id == "place/china"
    assert [a.legacy_id for a in china.aliases] == ["oil-china"]
    for investigation in load_investigations(INVESTIGATIONS):
        for entity in investigation.pack.entities:
            assert store.resolve_alias(investigation.pack.case_id, entity.id), entity.id
    assert store.resolve_alias(OIL, "no-such-entity") is None


def test_measurements_can_be_filtered_by_entity(store, release, vocabulary):
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    china = store.measurements("place/china")
    assert [m.metric_id for m in china] == ["O-M04"] * 3
    assert [m.value_text for m in china] == ["11.6", "12.0", "8.1"]
    assert len(store.measurements()) == 37


@pytest.mark.parametrize("table", NEW_TABLES)
def test_every_new_table_is_append_only(store, release, vocabulary, database, table):
    from app.normalisation.release import SourceBinding

    binding = SourceBinding(source_id="O-S28", basis="synthetic test binding")
    measurements = [
        m.model_copy(update={"bound_sources": [binding]}) if m.id.endswith(":O-M07:0") else m
        for m in release.measurements
    ]
    release = release.model_copy(update={"measurements": measurements})
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    with database.connect() as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            connection.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))


def test_a_second_different_decision_is_refused(store, release, vocabulary):
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    accept(store, release.release_id)  # the identical decision repeats harmlessly
    with pytest.raises(ReviewConflict):
        store.decide(release.release_id, "reject", "Synthetic test reviewer", "Changed mind")


def test_reusing_an_id_for_different_content_is_refused(store, release, vocabulary):
    store.record_release(release, vocabulary)
    other = release.model_copy(update={"entities": release.entities[:-1]})
    with pytest.raises(ReviewConflict, match="different content"):
        store.record_release(other, vocabulary)


def test_a_later_release_may_not_drop_an_accepted_alias(store, release, vocabulary):
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    dropped = release.model_copy(
        update={
            "release_id": "nx-norm-next",
            "entities": [
                e for e in release.entities if all(a.legacy_id != "oil-china" for a in e.aliases)
            ],
        }
    )
    with pytest.raises(ReviewConflict, match="place/china"):
        store.record_release(dropped, vocabulary)


def test_deciding_on_an_unknown_release_is_a_key_error(store):
    with pytest.raises(KeyError):
        store.decide("missing", "accept", "Synthetic test reviewer", "Test only")


def test_the_copper_pack_is_covered_too(store, release, vocabulary):
    store.record_release(release, vocabulary)
    accept(store, release.release_id)
    assert store.claim_projection("C07").claim.predicate == "offtake_agreement_with"
    assert store.resolve_alias(COPPER, "smelter").canonical_id == "facility/kamoa-kakula-smelter"


def test_bound_sources_round_trip_and_only_bound_measurements_carry_them(
    store, release, vocabulary
):
    from app.normalisation.release import SourceBinding

    binding = SourceBinding(source_id="O-S28", basis="synthetic test binding")
    measurements = [
        m.model_copy(update={"bound_sources": [binding]}) if m.id.endswith(":O-M07:0") else m
        for m in release.measurements
    ]
    bound = release.model_copy(update={"release_id": "nx-norm-bound", "measurements": measurements})
    store.record_release(bound, vocabulary)
    accept(store, "nx-norm-bound")
    served = store.measurements()
    carrying = [m for m in served if m.bound_sources]
    assert [m.id for m in carrying] == [f"{OIL}:O-M07:0"]
    assert carrying[0].bound_sources == [binding]
