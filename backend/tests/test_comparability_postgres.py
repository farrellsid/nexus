"""Comparison sets, reviewed memberships and relations in PostgreSQL. Synthetic test data.

Two real measurements are grouped into a set purely to exercise the code path; the packs
contain no actual conflict.
"""

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from app.investigation import load_investigations
from app.main import INVESTIGATIONS, VOCABULARY, create_app
from app.normalisation.vocabulary import load_vocabulary
from app.review import ReviewConflict
from app.storage.comparisons import PostgresComparisons
from app.storage.reviews import PostgresReviews

OIL = "oil-system-2025q3-2026q2"
A, B = f"{OIL}:O-M01:3", f"{OIL}:O-M02:3"
HISTORY = [
    "investigation_seed",
    "evidence_sources",
    "knowledge_assertions",
    "knowledge_proposals",
    "knowledge_proposal_evidence",
    "knowledge_decisions",
    "knowledge_versions",
    "normalisation_release",
    "claim_projection",
]
NEW_TABLES = ["comparison_set", "comparison_membership", "claim_relation"]
WHO = "Synthetic test reviewer"


@pytest.fixture
def comparisons(database, store, release, vocabulary):
    store.record_release(release, vocabulary)
    store.decide(release.release_id, "accept", WHO, "Test acceptance only")
    return PostgresComparisons(database, store)


def digest(database, table):
    with database.connect() as connection:
        row = connection.execute(
            sql.SQL(
                "SELECT count(*) AS n, md5(coalesce(string_agg(t::text, '' ORDER BY t::text), ''))"
                " AS d FROM {} t"
            ).format(sql.Identifier(table))
        ).fetchone()
    return row["n"], row["d"]


def test_a_set_starts_empty_and_is_idempotent(comparisons):
    comparisons.create_set("s1", "1", {"note": "synthetic"})
    comparisons.create_set("s1", "1", {"note": "synthetic"})
    with pytest.raises(ReviewConflict):
        comparisons.create_set("s1", "1", {"note": "different"})


def test_an_assessment_needs_a_reviewer_reason_and_a_known_report(comparisons):
    comparisons.create_set("s1", "1", {})
    with pytest.raises(psycopg.errors.CheckViolation):
        comparisons.assess("s1", A, "comparable", "same period", " ")
    with pytest.raises(psycopg.errors.CheckViolation):
        comparisons.assess("s1", A, "comparable", " ", WHO)
    with pytest.raises(KeyError):
        comparisons.assess("s1", "no-such-report", "comparable", "x", WHO)
    with pytest.raises(KeyError):
        comparisons.assess("missing-set", A, "comparable", "x", WHO)


def test_a_second_current_assessment_must_supersede_the_first(comparisons):
    comparisons.create_set("s1", "1", {})
    first = comparisons.assess("s1", A, "unresolved", "not yet reviewed", WHO)
    with pytest.raises(ReviewConflict):
        comparisons.assess("s1", A, "comparable", "same definition", WHO)
    second = comparisons.assess("s1", A, "comparable", "same definition", WHO, supersedes=first)
    assert second != first
    with pytest.raises(ReviewConflict):
        comparisons.assess("s1", A, "not_comparable", "changed mind", WHO, supersedes=first)


def test_only_the_latest_assessment_counts(comparisons, vocabulary):
    comparisons.create_set("s1", "1", {})
    first = comparisons.assess("s1", A, "unresolved", "not yet reviewed", WHO)
    comparisons.assess("s1", A, "comparable", "same definition", WHO, supersedes=first)
    comparisons.assess("s1", B, "not_comparable", "different chokepoint", WHO)
    [shown] = comparisons.displays(load_investigations(INVESTIGATIONS), vocabulary)
    assert shown.set_id == "s1"
    cards = {c.report_id: c for c in shown.display.cards}
    assert cards[B].difference == "different chokepoint"
    assert cards[A].difference is None
    assert shown.display.range is None


def test_relations_are_recorded_and_shape_the_display(comparisons, vocabulary):
    comparisons.create_set("s1", "1", {})
    comparisons.assess("s1", A, "comparable", "x", WHO)
    comparisons.assess("s1", B, "comparable", "x", WHO)
    comparisons.relate(f"measurement:{B}", f"measurement:{A}", "revises", "synthetic revision", WHO)
    [shown] = comparisons.displays(load_investigations(INVESTIGATIONS), vocabulary)
    assert [c.report_id for c in shown.display.cards] == [B]
    assert shown.display.cards[0].revised_from == [A]


def test_a_blank_relation_rationale_is_refused(comparisons):
    with pytest.raises(psycopg.errors.CheckViolation):
        comparisons.relate("claim:O-C02", "claim:O-C03", "contradicts", " ", WHO)


@pytest.mark.parametrize("table", NEW_TABLES)
def test_every_comparison_table_is_append_only(comparisons, database, table):
    comparisons.create_set("s1", "1", {})
    comparisons.assess("s1", A, "unresolved", "x", WHO)
    comparisons.relate("claim:O-C02", "claim:O-C03", "supports", "synthetic", WHO)
    with database.connect() as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            connection.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))


def test_comparison_writes_change_no_recorded_history(comparisons, database):
    before = {t: digest(database, t) for t in HISTORY}
    comparisons.create_set("s1", "1", {})
    first = comparisons.assess("s1", A, "unresolved", "x", WHO)
    comparisons.assess("s1", A, "comparable", "y", WHO, supersedes=first)
    comparisons.relate("claim:O-C02", "claim:O-C03", "supports", "synthetic", WHO)
    assert {t: digest(database, t) for t in HISTORY} == before


@pytest.fixture
def client(database, store, comparisons):
    app = create_app(
        load_investigations(INVESTIGATIONS), PostgresReviews(database), None, store, comparisons
    )
    return TestClient(app)


def test_the_api_lists_no_sets_when_none_exist(client):
    assert client.get("/api/comparisons").json() == []


def test_the_api_serves_a_set_with_cards_and_an_explained_missing_range(client, comparisons):
    comparisons.create_set("s1", "1", {"note": "synthetic"})
    comparisons.assess("s1", A, "comparable", "x", WHO)
    comparisons.assess("s1", B, "comparable", "x", WHO)
    shown = client.get("/api/comparisons/s1").json()
    assert {c["report_id"] for c in shown["display"]["cards"]} == {A, B}
    assert shown["display"]["range"] is None
    assert any("metadata" in note for note in shown["display"]["notes"])
    assert client.get("/api/comparisons").json()[0]["set_id"] == "s1"


def test_an_unknown_set_is_404_and_unconfigured_storage_is_503(client):
    assert client.get("/api/comparisons/none").status_code == 404
    bare = TestClient(create_app(load_investigations(INVESTIGATIONS)))
    assert bare.get("/api/comparisons").status_code == 503


def test_the_vocabulary_used_by_the_api_is_the_repository_file():
    assert load_vocabulary(VOCABULARY).version == "1"
