"""The acquisition log in PostgreSQL. Synthetic test data; a disposable schema per test."""

from datetime import UTC, datetime

import psycopg
import pytest
from psycopg import sql

from app.acquisition.extraction import extract_text
from app.acquisition.fetch import FetchResult
from app.acquisition.verification import Attempt, Baseline, verify
from app.review import ReviewConflict
from app.storage.acquisition import PostgresAcquisition

WHO = "Synthetic test reviewer"
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
    "comparison_set",
]
NEW_TABLES = [
    "fetch_attempt",
    "content_object",
    "source_baseline",
    "extraction_version",
    "verification_result",
]
BODY = "<p>" + "Stable synthetic page text for the fixture. " * 10 + "China imported 8.1.</p>"
SHA = "a" * 64


def result(outcome="ok", sha=SHA, body=BODY.encode(), **changes):
    now = datetime.now(UTC)
    base = {
        "source_url": "https://example.org/a",
        "final_url": "https://example.org/a",
        "redirect_chain": ["https://example.org/a"],
        "status": 200 if outcome == "ok" else None,
        "content_type": "text/html" if outcome == "ok" else None,
        "etag": None,
        "last_modified": None,
        "byte_count": len(body) if outcome == "ok" else 0,
        "sha256": sha if outcome == "ok" else None,
        "body": body if outcome == "ok" else b"",
        "outcome": outcome,
        "error": None if outcome == "ok" else "synthetic",
        "started_at": now,
        "ended_at": now,
    }
    return FetchResult(**{**base, **changes})


@pytest.fixture
def acquisition(database):
    return PostgresAcquisition(database)


def digest(database, table):
    with database.connect() as connection:
        row = connection.execute(
            sql.SQL(
                "SELECT count(*) AS n, md5(coalesce(string_agg(t::text, '' ORDER BY t::text), ''))"
                " AS d FROM {} t"
            ).format(sql.Identifier(table))
        ).fetchone()
    return row["n"], row["d"]


def test_every_outcome_is_logged_including_ones_with_no_hash(acquisition):
    ok = acquisition.log_attempt("S01", result(), stored=False)
    blocked = acquisition.log_attempt("S01", result("blocked_target"), stored=False)
    attempts = acquisition.attempts("S01")
    assert [a.id for a in attempts] == [ok, blocked]
    assert attempts[0].sha256 == SHA and attempts[0].stored is False
    assert attempts[1].sha256 is None and attempts[1].outcome == "blocked_target"


def test_the_same_content_is_recorded_once_across_attempts(acquisition, database):
    acquisition.log_attempt("S01", result(), stored=False)
    acquisition.log_attempt("S01", result(), stored=True)
    assert digest(database, "content_object")[0] == 1
    assert digest(database, "fetch_attempt")[0] == 2


def test_an_unknown_source_is_refused(acquisition):
    with pytest.raises(KeyError):
        acquisition.log_attempt("NOPE", result(), stored=False)


def test_a_baseline_needs_a_basis_a_reviewer_and_known_content(acquisition):
    acquisition.log_attempt("S01", result(), stored=False)
    with pytest.raises(psycopg.errors.CheckViolation):
        acquisition.set_baseline("S01", SHA, None, " ", WHO)
    with pytest.raises(psycopg.errors.CheckViolation):
        acquisition.set_baseline("S01", SHA, None, "first snapshot", " ")
    with pytest.raises(KeyError):
        acquisition.set_baseline("S01", "b" * 64, None, "first snapshot", WHO)


def test_a_second_baseline_must_supersede_the_first(acquisition):
    acquisition.log_attempt("S01", result(), stored=False)
    other = "c" * 64
    acquisition.log_attempt("S01", result(sha=other), stored=False)
    first = acquisition.set_baseline("S01", SHA, "t1", "first snapshot", WHO)
    with pytest.raises(ReviewConflict):
        acquisition.set_baseline("S01", other, "t2", "re-baselined", WHO)
    second = acquisition.set_baseline("S01", other, "t2", "re-baselined", WHO, supersedes=first)
    current = acquisition.current_baseline("S01")
    assert (current.id, current.sha256, current.supersedes_id) == (second, other, first)


def test_no_baseline_means_none(acquisition):
    assert acquisition.current_baseline("S01") is None


def test_extraction_recording_is_idempotent(acquisition, database):
    acquisition.log_attempt("S01", result(), stored=False)
    extraction = extract_text(BODY)
    first = acquisition.record_extraction(SHA, extraction)
    assert acquisition.record_extraction(SHA, extraction) == first
    assert digest(database, "extraction_version")[0] == 1
    with pytest.raises(KeyError):
        acquisition.record_extraction("d" * 64, extraction)


def test_a_verification_references_its_attempt_and_baseline(acquisition):
    attempt_id = acquisition.log_attempt("S01", result(), stored=False)
    baseline_id = acquisition.set_baseline(
        "S01", SHA, extract_text(BODY).text_sha256, "first snapshot", WHO
    )
    verdict = verify(
        Baseline(sha256=SHA, text_sha256=extract_text(BODY).text_sha256, basis="first snapshot"),
        Attempt(outcome="ok", sha256=SHA, extraction=extract_text(BODY), media_type="text/html"),
        ["China imported 8.1."],
    )
    acquisition.record_verification("S01", attempt_id, baseline_id, verdict)
    [row] = acquisition.verifications("S01")
    assert (row.state, row.attempt_id, row.baseline_id) == ("matches", attempt_id, baseline_id)
    assert row.passages == [{"phrase": "China imported 8.1.", "found": True}]


def test_a_verification_without_a_baseline_is_recorded_as_not_ready(acquisition):
    attempt_id = acquisition.log_attempt("S01", result(), stored=False)
    verdict = verify(
        None,
        Attempt(outcome="ok", sha256=SHA, extraction=extract_text(BODY), media_type="text/html"),
        [],
    )
    acquisition.record_verification("S01", attempt_id, None, verdict)
    [row] = acquisition.verifications("S01")
    assert (row.state, row.reason, row.comparison_readiness) == (
        "unreachable",
        "baseline_missing",
        "not_ready",
    )
    assert row.baseline_id is None


@pytest.mark.parametrize("table", NEW_TABLES)
def test_every_new_table_is_append_only(acquisition, database, table):
    attempt_id = acquisition.log_attempt("S01", result(), stored=False)
    acquisition.record_extraction(SHA, extract_text(BODY))
    baseline_id = acquisition.set_baseline("S01", SHA, None, "first snapshot", WHO)
    verdict = verify(
        None, Attempt(outcome="network_error", sha256=None, extraction=None, media_type=None), []
    )
    acquisition.record_verification("S01", attempt_id, baseline_id, verdict)
    with database.connect() as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            connection.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))


def test_acquisition_writes_change_no_recorded_history(acquisition, database):
    before = {t: digest(database, t) for t in HISTORY}
    attempt_id = acquisition.log_attempt("S01", result(), stored=False)
    acquisition.record_extraction(SHA, extract_text(BODY))
    baseline_id = acquisition.set_baseline("S01", SHA, None, "first snapshot", WHO)
    acquisition.record_verification(
        "S01",
        attempt_id,
        baseline_id,
        verify(
            None, Attempt(outcome="ok", sha256=SHA, extraction=None, media_type="text/html"), []
        ),
    )
    assert {t: digest(database, t) for t in HISTORY} == before
