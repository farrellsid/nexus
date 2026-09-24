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
        "observed",
        "reported",
        "estimated",
        "inferred",
        "forecast",
        "scenario",
        "unknown",
    ]
    assert vocabulary.modalities == [
        "actual",
        "planned",
        "capability",
        "generic",
        "required",
        "unknown",
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
