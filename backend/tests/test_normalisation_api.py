"""Read endpoints for the accepted normalisation release. Claims themselves are untouched."""

import pytest
from fastapi.testclient import TestClient

from app.investigation import load_investigations
from app.main import INVESTIGATIONS, create_app
from app.storage.reviews import PostgresReviews

OIL = "oil-system-2025q3-2026q2"


@pytest.fixture
def client(database, store):
    app = create_app(load_investigations(INVESTIGATIONS), PostgresReviews(database), None, store)
    return TestClient(app)


@pytest.fixture
def accepted(store, release, vocabulary):
    store.record_release(release, vocabulary)
    store.decide(release.release_id, "accept", "Synthetic test reviewer", "Test acceptance only")


def test_status_says_not_normalised_before_acceptance(client):
    assert client.get("/api/normalisation/status").json() == {"accepted_release_id": None}


def test_reads_are_empty_before_acceptance_so_the_ui_can_say_not_yet_normalised(client):
    assert client.get("/api/claims/O-C02/projection").json() is None
    assert (
        client.get(
            "/api/entities/resolve", params={"case_id": OIL, "legacy_id": "oil-china"}
        ).json()
        is None
    )
    assert client.get("/api/measurements").json() == []


def test_an_accepted_release_serves_projection_alias_and_measurements(client, accepted):
    assert client.get("/api/normalisation/status").json() == {
        "accepted_release_id": "nx-norm-2026-09-24"
    }
    projection = client.get("/api/claims/O-C02/projection").json()
    assert projection["claim"]["predicate"] == "carries_flow_within"
    assert projection["claim"]["temporal"]["valid_end_exclusive"] == "2026-07-01"
    china = client.get(
        "/api/entities/resolve", params={"case_id": OIL, "legacy_id": "oil-china"}
    ).json()
    assert china["canonical_id"] == "place/china"
    measurements = client.get("/api/measurements", params={"entity": "place/china"}).json()
    assert [m["value_text"] for m in measurements] == ["11.6", "12.0", "8.1"]


def test_unknown_claim_and_case_are_404(client, accepted):
    assert client.get("/api/claims/NOPE/projection").status_code == 404
    unknown = client.get("/api/entities/resolve", params={"case_id": "nope", "legacy_id": "x"})
    assert unknown.status_code == 404


def test_recorded_claims_are_identical_with_and_without_a_release(
    client, store, release, vocabulary
):
    before = client.get("/api/investigation", params={"case_id": OIL}).content
    store.record_release(release, vocabulary)
    store.decide(release.release_id, "accept", "Synthetic test reviewer", "Test acceptance only")
    assert client.get("/api/investigation", params={"case_id": OIL}).content == before


def test_normalisation_reads_need_configured_storage():
    app = create_app(load_investigations(INVESTIGATIONS))
    unconfigured = TestClient(app)
    assert unconfigured.get("/api/normalisation/status").status_code == 503
