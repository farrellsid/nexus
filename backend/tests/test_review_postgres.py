"""Real PostgreSQL tests; every test gets a disposable, uniquely named schema."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.investigation import load_investigation, load_investigations
from app.main import INVESTIGATIONS, PILOT, create_app
from app.review import DecisionRequest, ProposalRequest, ReviewConflict, ReviewService
from app.storage.backup import create_backup, restore_backup
from app.storage.database import ROOT, Database, configured_url
from app.storage.reviews import PostgresReviews


@pytest.fixture
def store():
    url = configured_url()
    if not url:
        pytest.skip(
            "Set NEXUS_DATABASE_URL or run scripts/setup-postgres.py for real database tests"
        )
    database = Database(url, "test_" + uuid4().hex)
    database.migrate()
    repository = PostgresReviews(database)
    repository.initialize(load_investigation(PILOT))
    try:
        yield repository
    finally:
        with database.connect() as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(database.schema))
            )


def decision(revision=0, choice="accept"):
    return DecisionRequest(
        request_id=uuid4(),
        expected_revision=revision,
        decision=choice,
        reviewer="Synthetic test reviewer",
        reason="Test review only",
    )


def correction(revision=1, **changes):
    return ProposalRequest.model_validate(
        {
            "request_id": uuid4(),
            "base_revision": revision,
            "statement": "Synthetic corrected wording for persistence testing",
            "caveat": "Synthetic test; not a new factual claim",
            "evidence_ids": ["S06"],
            "author": "Synthetic test author",
            "reason": "Test correction only",
            **changes,
        }
    )


def accept_initial(store, claim_id="C10"):
    proposal = store.history(claim_id).proposals[0]
    return store.decide(proposal.id, decision())


def test_import_is_idempotent_and_does_not_accept_candidates(store):
    store.database.migrate()
    store.initialize(load_investigation(PILOT))
    history = store.history("C10")
    assert history.current_revision == 0
    assert len(history.proposals) == 1
    assert history.versions == []
    assert history.proposals[0].claim.review_status == "manually_source_checked_candidate"
    assert history.proposals[0].proposed_at.year >= 2026


def test_multiple_investigations_are_imported_and_filtered_independently(store):
    oil = next(
        item
        for item in load_investigations(INVESTIGATIONS)
        if item.pack.case_id == "oil-system-2025q3-2026q2"
    )
    store.initialize(oil)
    assert len(store.current_claims([claim.id for claim in oil.pack.claims])) == 26
    assert {claim.id for claim in store.current_claims(["C10", "O-C02"])} == {
        "C10",
        "O-C02",
    }
    client = TestClient(create_app(load_investigations(INVESTIGATIONS), store))
    copper = client.get("/api/investigation", params={"case_id": "kamoa-to-cables"}).json()
    oil_data = client.get(
        "/api/investigation", params={"case_id": "oil-system-2025q3-2026q2"}
    ).json()
    assert len(copper["pack"]["claims"]) == 18
    assert len(oil_data["pack"]["claims"]) == 26


def test_correction_changes_baseline_only_on_acceptance_and_preserves_history(store):
    first = accept_initial(store)
    service = ReviewService(load_investigation(PILOT).pack, store)
    request = correction(valid_from="2026-02-01", valid_to="2026-02-28")
    pending = service.propose("C10", request)
    assert pending.current_revision == 1
    assert next(c for c in store.current_claims() if c.id == "C10") == first.versions[0].claim
    accepted = store.decide(request.request_id, decision(1))
    assert accepted.current_revision == 2
    assert accepted.versions[0] == first.versions[0]
    assert accepted.versions[1].claim.statement == request.statement
    assert accepted.versions[1].claim.valid_from == request.valid_from
    assert accepted.versions[1].claim.ground_truth is False
    assert accepted.versions[1].recorded_at >= accepted.versions[0].recorded_at
    # A fresh connection/repository must read the same durable state.
    assert (
        PostgresReviews(Database(store.database.url, store.database.schema)).history("C10")
        == accepted
    )


def test_rejecting_correction_preserves_accepted_baseline(store):
    first = accept_initial(store)
    request = correction()
    ReviewService(load_investigation(PILOT).pack, store).propose("C10", request)
    rejected = store.decide(request.request_id, decision(1, "reject"))
    assert rejected.current_revision == 1
    assert rejected.versions == first.versions
    assert rejected.proposals[-1].decision.decision == "reject"


def test_rejecting_initial_candidate_is_visible(store):
    store.decide(store.history("C10").proposals[0].id, decision(choice="reject"))
    assert next(c for c in store.current_claims() if c.id == "C10").review_status == "rejected"
    assert store.history("C10").versions == []


def test_retries_are_idempotent_but_changed_payload_is_rejected(store):
    initial_id = store.history("C10").proposals[0].id
    review = decision()
    first = store.decide(initial_id, review)
    assert store.decide(initial_id, review) == first
    with pytest.raises(ReviewConflict):
        store.decide(initial_id, review.model_copy(update={"reason": "Changed reason"}))
    request = correction()
    service = ReviewService(load_investigation(PILOT).pack, store)
    proposed = service.propose("C10", request)
    assert service.propose("C10", request) == proposed
    with pytest.raises(ReviewConflict):
        service.propose("C10", request.model_copy(update={"statement": "Changed payload"}))


def test_concurrent_reviews_cannot_overwrite_each_other(store):
    accept_initial(store)
    service = ReviewService(load_investigation(PILOT).pack, store)
    requests = [correction(statement=f"Synthetic alternate {i}") for i in range(2)]
    for request in requests:
        service.propose("C10", request)

    def accept(request):
        try:
            store.decide(request.request_id, decision(1))
            return "accepted"
        except ReviewConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(accept, requests)) == ["accepted", "conflict"]
    history = store.history("C10")
    assert history.current_revision == 2
    pending = next(p for p in history.proposals if p.decision is None)
    with pytest.raises(ReviewConflict, match="stale"):
        store.decide(pending.id, decision(2))
    assert len(store.history("C10").versions) == 2


def test_invalid_evidence_rolls_back_entire_proposal(store):
    accept_initial(store)
    request = correction(evidence_ids=["missing-source"])
    service = ReviewService(load_investigation(PILOT).pack, store)
    with pytest.raises(ValueError, match="references"):
        service.propose("C10", request)
    # The storage seam also has a database FK, even if its caller bypasses validation.
    claim = (
        store.history("C10")
        .versions[0]
        .claim.model_copy(update={"evidence_ids": ["missing-source"]})
    )
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        store.propose(claim, request)
    assert len(store.history("C10").proposals) == 1


def test_failed_version_write_rolls_back_decision_and_head(store):
    with store.database.connect() as connection:
        connection.execute("""
            CREATE TRIGGER simulate_write_failure BEFORE INSERT ON knowledge_versions
            FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite()
        """)
    with pytest.raises(psycopg.errors.RaiseException):
        accept_initial(store)
    history = store.history("C10")
    assert history.current_revision == 0
    assert history.proposals[0].decision is None
    assert history.versions == []


@pytest.mark.parametrize(
    "table",
    ["knowledge_versions", "knowledge_proposals", "knowledge_decisions", "evidence_sources"],
)
def test_retained_history_cannot_be_deleted(store, table):
    accept_initial(store)
    with pytest.raises(psycopg.errors.RaiseException), store.database.connect() as connection:
        connection.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))
    assert store.history("C10").current_revision == 1


def test_changed_fixture_is_not_silently_reimported(store):
    fixture = load_investigation(PILOT)
    changed = fixture.model_copy(update={"answer_mode": "changed"})
    with pytest.raises(RuntimeError, match="differs"):
        store.initialize(changed)


def test_review_api_validation_origin_protection_and_current_graph(store):
    client = TestClient(create_app(load_investigation(PILOT), store))
    proposal = store.history("C10").proposals[0]
    path = f"/api/proposals/{proposal.id}/decision"
    body = decision().model_dump(mode="json")
    assert client.post(path, json=body).status_code == 403
    assert (
        client.post(
            path, json=body, headers={"x-nexus-review": "1", "origin": "https://foreign.example"}
        ).status_code
        == 403
    )
    headers = {"x-nexus-review": "1", "origin": "http://127.0.0.1:5173"}
    assert client.post(path, json={**body, "reviewer": " "}, headers=headers).status_code == 422
    assert client.post(path, json=body, headers=headers).status_code == 200
    claims = client.get("/api/entities/trafigura/neighborhood").json()["claims"]
    assert next(c for c in claims if c["id"] == "C10")["review_status"] == "accepted"
    assert client.get("/api/claims/missing/history").status_code == 404


def test_native_backup_restores_evidence_decisions_and_versions(store):
    before = accept_initial(store)
    archive = ROOT / ".local/test-backups" / f"{uuid4().hex}.dump"
    restored_name = "nexus_restore_test_" + uuid4().hex[:16]
    settings = conninfo_to_dict(store.database.url)
    with psycopg.connect(store.database.url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restored_name)))
    try:
        create_backup(store.database, archive)
        with pytest.raises(FileExistsError):
            create_backup(store.database, archive)
        restored_db = Database(
            make_conninfo(**{**settings, "dbname": restored_name}), store.database.schema
        )
        restore_backup(restored_db, archive)
        restored = PostgresReviews(restored_db)
        assert restored.history("C10") == before
        assert restored.current_claims() == store.current_claims()
        restored_db.migrate()
        restored.initialize(load_investigation(PILOT))
        with pytest.raises(ValueError, match="without the target schema"):
            restore_backup(restored_db, archive)
    finally:
        with psycopg.connect(store.database.url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(restored_name)))
        archive.unlink(missing_ok=True)
