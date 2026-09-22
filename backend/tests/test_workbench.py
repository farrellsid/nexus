"""Synthetic invariant checks and separate integration checks against the research fixture."""

import json
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.geography import GeoRoute
from app.investigation import load_investigation, load_investigations
from app.knowledge import EvidencePack, neighborhood
from app.main import INVESTIGATIONS, app


@pytest.fixture
def synthetic():
    source = {
        "id": "synthetic-source",
        "title": "Synthetic fixture — not real evidence",
        "publisher": "Test",
        "published_on": "2026-01-01",
        "language": "en",
        "url": "https://example.com/synthetic",
        "locator": "Test paragraph",
        "excerpt": "Test only",
        "format": "HTML",
        "origin_group": "synthetic",
        "checked_on": "2026-01-02",
        "review_status": "synthetic",
        "rights": "Synthetic test data",
        "independence": "Synthetic",
    }
    entities = [
        {
            "id": name,
            "name": f"Synthetic {name}",
            "type": "facility",
            "coordinates": None,
            "location_note": "Unknown",
        }
        for name in ("mine", "smelter", "rod", "cables", "isolated")
    ]
    claims = [
        {
            "id": f"synthetic-{index}",
            "subject": subject,
            "object": object_,
            "predicate": "supplies",
            "evidence_ids": [source["id"]],
            "kind": "synthetic",
            "source_as_of": "2026-01-01",
            "valid_from": None,
            "valid_to": None,
            "recorded_on": "2026-01-02",
            "statement": "Synthetic relationship",
            "caveat": "No physical lineage established",
            "review_status": "candidate",
            "ground_truth": False,
        }
        for index, (subject, object_) in enumerate(
            [("mine", "smelter"), ("smelter", "rod"), ("rod", "mine"), ("rod", "cables")]
        )
    ]
    return {
        "schema_version": "synthetic-test",
        "case_id": "synthetic",
        "checked_on": "2026-01-02",
        "scope": "Synthetic only",
        "verdict": "Synthetic only",
        "sources": [source],
        "entities": entities,
        "claims": claims,
        "events": [],
    }


def test_cycles_are_bounded_and_direction_is_preserved(synthetic):
    pack = EvidencePack.model_validate(synthetic)
    one_step = neighborhood(pack, "mine")
    assert {entity.id for entity in one_step.entities} == {"mine", "smelter", "rod"}
    assert {(claim.subject, claim.object) for claim in one_step.claims} == {
        ("mine", "smelter"),
        ("rod", "mine"),
    }
    two_steps = neighborhood(pack, "mine", 2)
    assert len(two_steps.claims) == 4
    assert len(two_steps.entities) == 4
    assert all(entity.coordinates is None for entity in two_steps.entities)
    assert all(claim.review_status == "candidate" for claim in two_steps.claims)


def test_isolated_entity_does_not_gain_invented_links(synthetic):
    result = neighborhood(EvidencePack.model_validate(synthetic), "isolated")
    assert len(result.entities) == 1
    assert result.claims == result.sources == []


@pytest.mark.parametrize("corruption", ["endpoint", "evidence", "duplicate", "dates"])
def test_invalid_records_are_rejected_before_serving(synthetic, corruption):
    broken = deepcopy(synthetic)
    if corruption == "endpoint":
        broken["claims"][0]["object"] = "invented-refinery"
    elif corruption == "evidence":
        broken["claims"][0]["evidence_ids"] = ["missing-source"]
    elif corruption == "duplicate":
        broken["entities"].append(broken["entities"][0])
    else:
        broken["claims"][0].update(valid_from="2026-01-02", valid_to="2026-01-01")
    with pytest.raises(ValidationError):
        EvidencePack.model_validate(broken)


def test_conflicting_candidate_accounts_remain_separate(synthetic):
    conflict = deepcopy(synthetic["claims"][0])
    conflict.update(id="synthetic-conflict", statement="Synthetic source disputes the relationship")
    synthetic["claims"].append(conflict)
    result = neighborhood(EvidencePack.model_validate(synthetic), "mine")
    assert {"synthetic-0", "synthetic-conflict"} <= {claim.id for claim in result.claims}


def test_pilot_exposes_provenance_and_honest_unknowns():
    client = TestClient(app)
    response = client.get("/api/investigation")
    assert response.status_code == 200
    data = response.json()
    assert data["answer_mode"] == "curated_reading_guide"
    assert len(data["pack"]["claims"]) == 18
    assert all(claim["ground_truth"] is False for claim in data["pack"]["claims"])
    assert all(entity["coordinates"] is None for entity in data["pack"]["entities"])
    forecast = next(event for event in data["pack"]["events"] if event["id"] == "E03")
    assert forecast["kind"] == "forecast"
    assert forecast["event_time"] == "2025-10"
    unknown = next(question for question in data["questions"] if question["id"] == "Q07")
    assert unknown["expected_answer"].startswith("Unknown")
    assert unknown["claim_ids"] == []


def test_api_bounds_errors_and_evidence_scope():
    client = TestClient(app)
    assert client.get("/api/entities/missing/neighborhood").status_code == 404
    for depth in (0, 3, 100):
        assert client.get(f"/api/entities/trafigura/neighborhood?depth={depth}").status_code == 422
    data = client.get("/api/entities/trafigura/neighborhood").json()
    assert {source["id"] for source in data["sources"]} == {
        source_id for claim in data["claims"] for source_id in claim["evidence_ids"]
    }
    assert (
        client.post("/api/investigation", json={}, headers={"x-nexus-review": "1"}).status_code
        == 405
    )


def test_oil_brief_is_discoverable_and_keeps_measurement_statuses_distinct():
    loaded = {item.pack.case_id: item for item in load_investigations(INVESTIGATIONS)}
    oil = loaded["oil-system-2025q3-2026q2"]
    assert oil.pack.briefing is not None
    assert oil.geography is not None
    assert {stop.entity_id for stop in oil.geography.stops} == {
        "oil-hormuz",
        "oil-bab",
        "oil-malacca",
        "oil-yanbu",
        "oil-sunda",
        "oil-lombok",
    }
    assert all(
        stop.precision in {"representative_label_point", "facility_point"}
        for stop in oil.geography.stops
    )
    assert {route.entity_id for route in oil.geography.routes} == {
        "oil-suez-sumed",
        "oil-cape-good-hope",
        "oil-myanmar-china-pipeline",
    }
    assert all(len(route.points) >= 2 for route in oil.geography.routes)
    assert all(route.caveat for route in oil.geography.routes)
    assert all(str(route.source_url) for route in oil.geography.routes)
    assert oil.pack.briefing.window_end.isoformat() == "2026-06-30"
    assert len(oil.pack.briefing.metrics) == 11
    assert {point.status for metric in oil.pack.briefing.metrics for point in metric.points} == {
        "estimate",
        "reported",
        "forecast",
    }
    assert all(entity.coordinates is None for entity in oil.pack.entities)
    unknown = next(question for question in oil.questions if question.id == "O-Q08")
    assert unknown.claim_ids == []

    client = TestClient(app)
    available = client.get("/api/investigations").json()
    assert {item["case_id"] for item in available} == {
        "kamoa-to-cables",
        "oil-system-2025q3-2026q2",
    }
    response = client.get("/api/investigation", params={"case_id": "oil-system-2025q3-2026q2"})
    assert response.status_code == 200
    assert response.json()["pack"]["briefing"]["metrics"][0]["id"] == "O-M01"
    assert len(response.json()["geography"]["stops"]) == 6
    assert len(response.json()["geography"]["routes"]) == 3
    assert {route["id"] for route in response.json()["geography"]["routes"]} == {
        "O-R01",
        "O-R02",
        "O-R03",
    }
    graph = client.get(
        "/api/entities/oil-hormuz/neighborhood",
        params={"case_id": "oil-system-2025q3-2026q2"},
    )
    assert graph.status_code == 200
    assert "O-C02" in {claim["id"] for claim in graph.json()["claims"]}
    malacca = client.get(
        "/api/entities/oil-malacca/neighborhood",
        params={"case_id": "oil-system-2025q3-2026q2"},
    )
    assert malacca.status_code == 200
    assert {"O-C16", "O-C17", "O-C20", "O-C21"} <= {
        claim["id"] for claim in malacca.json()["claims"]
    }
    assert {"oil-world", "oil-china", "oil-sunda", "oil-lombok"} <= {
        entity["id"] for entity in malacca.json()["entities"]
    }
    assert {metric.id for metric in oil.pack.briefing.metrics} >= {"O-M06"}
    alternatives = next(question for question in oil.questions if question.id == "O-Q11")
    assert {"O-C19", "O-C20", "O-C21", "O-C22"} == set(alternatives.claim_ids)


def test_metric_sources_are_validated(synthetic):
    synthetic["entities"] = [
        entity for entity in synthetic["entities"] if entity["id"] != "isolated"
    ]
    synthetic["briefing"] = {
        "title": "Synthetic brief",
        "window_start": "2026-01-01",
        "window_end": "2026-01-31",
        "developments_through": "2026-02-01",
        "framing": "Synthetic only",
        "metrics": [
            {
                "id": "synthetic-metric",
                "title": "Synthetic measure",
                "unit": "units",
                "description": "Synthetic only",
                "source_ids": ["missing-source"],
                "points": [{"period": "2026-01", "value": 1, "status": "reported"}],
                "caveat": "Synthetic only",
            }
        ],
    }
    with pytest.raises(ValidationError, match="missing-source"):
        EvidencePack.model_validate(synthetic)


def test_published_brief_rejects_isolated_entities(synthetic):
    synthetic["briefing"] = {
        "title": "Synthetic brief",
        "window_start": "2026-01-01",
        "window_end": "2026-01-31",
        "developments_through": "2026-02-01",
        "framing": "Synthetic only",
        "metrics": [
            {
                "id": "synthetic-metric",
                "title": "Synthetic measure",
                "unit": "units",
                "description": "Synthetic only",
                "source_ids": ["synthetic-source"],
                "points": [{"period": "2026-01", "value": 1, "status": "reported"}],
                "caveat": "Synthetic only",
            }
        ],
    }
    with pytest.raises(ValidationError, match="isolated entities: isolated"):
        EvidencePack.model_validate(synthetic)


def _synthetic_route(**overrides):
    route = {
        "id": "synthetic-route",
        "entity_id": "mine",
        "label": "Synthetic corridor",
        "points": [
            {"latitude": 0.0, "longitude": 0.0},
            {"latitude": 1.0, "longitude": 1.0},
        ],
        "precision": "illustrative_corridor_endpoints",
        "role": "Synthetic only",
        "why_it_matters": "Synthetic only",
        "caveat": "Synthetic only — a straight line between two invented points.",
        "source_title": "Synthetic fixture — not real evidence",
        "source_url": "https://example.com/synthetic-route",
        "checked_on": "2026-01-02",
    }
    route.update(overrides)
    return route


def test_route_needs_at_least_two_points():
    with pytest.raises(ValidationError, match="at least two points"):
        GeoRoute.model_validate(_synthetic_route(points=[{"latitude": 0.0, "longitude": 0.0}]))


def test_geography_route_validation_rejects_unknown_entities_and_duplicates(tmp_path, synthetic):
    (tmp_path / "evidence-pack.json").write_text(json.dumps(synthetic), encoding="utf-8")
    (tmp_path / "acceptance-cases.json").write_text("[]", encoding="utf-8")
    geography = {
        "title": "Synthetic geography",
        "framing": "Synthetic only",
        "stops": [],
        "routes": [_synthetic_route()],
    }
    (tmp_path / "geography.json").write_text(json.dumps(geography), encoding="utf-8")
    loaded = load_investigation(tmp_path)
    assert loaded.geography is not None
    assert loaded.geography.routes[0].entity_id == "mine"

    unknown_entity = deepcopy(geography)
    unknown_entity["routes"][0]["entity_id"] = "not-a-real-entity"
    (tmp_path / "geography.json").write_text(json.dumps(unknown_entity), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown entity"):
        load_investigation(tmp_path)

    duplicate_ids = deepcopy(geography)
    duplicate_ids["routes"].append(deepcopy(duplicate_ids["routes"][0]))
    (tmp_path / "geography.json").write_text(json.dumps(duplicate_ids), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate geography route IDs"):
        load_investigation(tmp_path)
