"""The proposed release must cover the real packs exactly. It stays a proposal until accepted."""

import json
from pathlib import Path

import pytest

from app.investigation import load_investigations
from app.main import INVESTIGATIONS
from app.normalisation.measurements import read_metric_points
from app.normalisation.release import Release, validate_release
from app.normalisation.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
RELEASES = ROOT / "normalisation" / "releases"
RELEASE = RELEASES / "2026-09-24-r3.json"


def test_original_decimal_text_is_preserved(tmp_path):
    pack = tmp_path / "evidence-pack.json"
    pack.write_text(
        '{"briefing":{"metrics":[{"id":"M","points":[{"value":5.97},{"value":13.7},{"value":100.0}]}]}}'
    )
    assert read_metric_points(pack) == {"M": ["5.97", "13.7", "100.0"]}


def test_a_pack_without_a_briefing_has_no_metrics(tmp_path):
    pack = tmp_path / "evidence-pack.json"
    pack.write_text('{"claims":[]}')
    assert read_metric_points(pack) == {}


pytestmark_release = pytest.mark.skipif(not RELEASE.exists(), reason="release not authored yet")


@pytest.fixture(scope="module")
def release() -> Release:
    return Release.model_validate_json(RELEASE.read_text("utf-8"))


@pytest.fixture(scope="module")
def investigations():
    return load_investigations(INVESTIGATIONS)


@pytest.fixture(scope="module")
def metric_texts(investigations):
    texts = {}
    for directory in sorted(INVESTIGATIONS.iterdir()):
        pack = directory / "evidence-pack.json"
        if pack.exists():
            case_id = json.loads(pack.read_text("utf-8"))["case_id"]
            texts |= {(case_id, k): v for k, v in read_metric_points(pack).items()}
    return texts


@pytestmark_release
def test_the_release_covers_every_real_record_exactly(release, investigations, metric_texts):
    vocabulary = load_vocabulary(ROOT / "normalisation" / "vocabulary-v1.json")
    assert validate_release(release, vocabulary, investigations, metric_texts) == []


@pytestmark_release
def test_the_release_has_the_expected_record_counts(release):
    assert (
        len(release.claims),
        len(release.sources),
        sum(len(e.aliases) for e in release.entities),
        len(release.measurements),
    ) == (44, 44, 43, 37)


@pytestmark_release
@pytest.mark.parametrize("claim_id", ["O-C07", "O-C08", "O-C12", "O-C13", "C11", "C13", "O-C25"])
def test_the_known_semantic_mismatches_are_flagged_for_review(release, claim_id):
    claim = next(c for c in release.claims if c.claim_id == claim_id)
    assert claim.needs_semantic_review
    assert claim.note


@pytestmark_release
def test_no_claim_or_measurement_is_observed(release):
    statuses = {c.epistemic_status for c in release.claims}
    statuses |= {m.epistemic_status for m in release.measurements}
    assert "observed" not in statuses


@pytestmark_release
def test_exactly_the_thirteen_bounded_claims_have_dates(release):
    bounded = {c.claim_id for c in release.claims if c.temporal.state != "unknown"}
    assert bounded == {
        "O-C02", "O-C03", "O-C07", "O-C08", "O-C10", "O-C12", "O-C13",
        "O-C16", "O-C17", "O-C23", "O-C24", "O-C25", "O-C26",
    }  # fmt: skip


@pytestmark_release
def test_russia_and_iran_are_registry_entities_and_link_their_measurements(release):
    registry = {e.canonical_id: e for e in release.entities}
    assert registry["place/russia"].aliases == [] and registry["place/iran"].aliases == []
    linked = {m.original_label: m.entity for m in release.measurements if m.metric_id == "O-M11"}
    assert linked["Russia"] == "place/russia" and linked["Iran"] == "place/iran"


def _load(name: str) -> Release:
    return Release.model_validate_json((RELEASES / name).read_text("utf-8"))


@pytestmark_release
def test_release_r2_adds_only_the_three_registered_eia_sources_to_the_accepted_release():
    accepted, r2 = _load("2026-09-24.json"), _load("2026-09-24-r2.json")
    assert r2.release_id == "nx-norm-2026-09-24-r2"
    assert r2.entities == accepted.entities
    assert r2.claims == accepted.claims
    assert r2.measurements == accepted.measurements
    added = [s for s in r2.sources if s not in accepted.sources]
    assert [s.source_id for s in added] == ["O-S28", "O-S29", "O-S30"]


@pytestmark_release
def test_release_r3_adds_only_the_seven_eia_source_bindings_to_r2(release):
    r2 = _load("2026-09-24-r2.json")
    assert release.release_id == "nx-norm-2026-09-24-r3"
    assert (release.entities, release.claims, release.sources) == (
        r2.entities,
        r2.claims,
        r2.sources,
    )
    assert [
        m.model_copy(update={"bound_sources": []}) for m in release.measurements
    ] == r2.measurements
    bound = {
        m.id.split(":", 1)[1]: [b.source_id for b in m.bound_sources]
        for m in release.measurements
        if m.bound_sources
    }
    assert bound == {
        "O-M07:0": ["O-S28"],
        "O-M07:1": ["O-S28"],
        "O-M07:2": ["O-S28"],
        "O-M09:0": ["O-S29"],
        "O-M09:1": ["O-S29"],
        "O-M08:0": ["O-S30"],
        "O-M08:1": ["O-S30"],
    }
    assert all(
        "not an independent measurement" in b.basis
        for m in release.measurements
        for b in m.bound_sources
    )
