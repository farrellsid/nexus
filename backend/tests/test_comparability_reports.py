"""Reports built from the real accepted release: the packs hold no conflict set yet."""

from pathlib import Path

import pytest

from app.comparability.model import candidate_groups, comparison_key, metadata_gaps
from app.comparability.reports import build_reports
from app.investigation import load_investigations
from app.main import INVESTIGATIONS
from app.normalisation.release import Release
from app.normalisation.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def reports_r3():
    release = Release.model_validate_json(
        (ROOT / "normalisation/releases/2026-09-24-r3.json").read_text("utf-8")
    )
    vocabulary = load_vocabulary(ROOT / "normalisation/vocabulary-v1.json")
    return build_reports(release.measurements, load_investigations(INVESTIGATIONS), vocabulary)


@pytest.fixture(scope="module")
def reports():
    release = Release.model_validate_json(
        (ROOT / "normalisation/releases/2026-09-24.json").read_text("utf-8")
    )
    vocabulary = load_vocabulary(ROOT / "normalisation/vocabulary-v1.json")
    return build_reports(release.measurements, load_investigations(INVESTIGATIONS), vocabulary)


def test_every_measurement_becomes_a_report(reports):
    assert len(reports) == 37


def test_units_and_statistics_come_from_the_vocabulary(reports):
    hormuz = next(r for r in reports if r.id.endswith(":O-M01:3"))
    assert (hormuz.unit_symbol, hormuz.statistic, hormuz.value_text) == (
        "million b/d",
        "mean_rate",
        "4.9",
    )
    stocks = next(r for r in reports if r.id.endswith(":O-M07:2"))
    assert (stocks.unit_symbol, stocks.statistic) == ("million bbl", "snapshot")


def test_sources_and_origins_come_from_the_metric_group(reports):
    hormuz = next(r for r in reports if r.id.endswith(":O-M01:3"))
    assert hormuz.source_ids == ["O-S01"]
    assert hormuz.origin_groups  # group-level binding until M4 adds point-level passages


def test_every_real_report_has_scope_metadata_gaps(reports):
    assert all(metadata_gaps(r) for r in reports)


def test_the_real_packs_contain_no_conflict_set(reports):
    assert candidate_groups(reports) == []


def test_reports_with_complete_periods_have_keys(reports):
    assert sum(comparison_key(r) is not None for r in reports) == 37


def test_bound_sources_are_added_to_the_group_sources_and_origins(reports_r3):
    stocks = next(r for r in reports_r3 if r.id.endswith(":O-M07:2"))
    assert stocks.source_ids[-1] == "O-S28" and "O-S14" in stocks.source_ids
    assert "eia-open-data-api-v2" in stocks.origin_groups
    unbound = next(r for r in reports_r3 if r.id.endswith(":O-M01:3"))
    assert unbound.source_ids == ["O-S01"]
