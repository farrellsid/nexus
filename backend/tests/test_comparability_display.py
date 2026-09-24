"""Comparability rules and side-by-side display data. Synthetic test data only.

The real packs contain no two-source conflict, so every behaviour here is exercised on
clearly synthetic reports.
"""

from datetime import date

from app.comparability.display import build_display
from app.comparability.model import (
    Membership,
    Period,
    Relation,
    Report,
    candidate_groups,
    comparison_key,
    metadata_gaps,
)

Q2 = Period(kind="interval", start=date(2026, 4, 1), end_exclusive=date(2026, 7, 1), at=None)
FULL_SCOPE = {
    "geography": "world",
    "population": "all",
    "methodology": "survey",
    "seasonal_adjustment": "none",
}


def report(rid, value="4.9", origin="A", **changes):
    base = {
        "id": rid,
        "entity": "place/x",
        "measure": "chokepoint_transit_rate",
        "statistic": "mean_rate",
        "unit_symbol": "million b/d",
        "period": Q2,
        "value_text": value,
        "epistemic_status": "estimated",
        "release_status": "unspecified",
        "source_ids": [f"S-{rid}"],
        "origin_groups": [origin],
        "scope": dict(FULL_SCOPE),
    }
    return Report(**{**base, **changes})


def member(
    rid, assessment="comparable", reason="same definition and period", reviewer="Synthetic reviewer"
):
    return Membership(report_id=rid, assessment=assessment, reason=reason, reviewer=reviewer)


class TestKeysAndCandidates:
    def test_matching_reports_from_two_origins_are_a_candidate_group(self):
        groups = candidate_groups([report("r1", origin="A"), report("r2", "5.1", origin="B")])
        assert [[r.id for r in g] for g in groups] == [["r1", "r2"]]

    def test_the_same_origin_twice_is_not_a_candidate_group(self):
        assert candidate_groups([report("r1"), report("r2", "5.1")]) == []

    def test_a_missing_period_makes_the_key_unresolved(self):
        unknown = Period(kind="unknown", start=None, end_exclusive=None, at=None)
        assert comparison_key(report("r1", period=unknown)) is None

    def test_forecast_and_reported_never_group(self):
        groups = candidate_groups(
            [report("r1", origin="A"), report("r2", origin="B", epistemic_status="forecast")]
        )
        assert groups == []

    def test_different_units_or_periods_do_not_group(self):
        other = report("r2", origin="B", unit_symbol="Mt")
        assert candidate_groups([report("r1", origin="A"), other]) == []

    def test_missing_scope_metadata_is_listed_not_assumed_equal(self):
        assert metadata_gaps(report("r1", scope={})) == [
            "geography",
            "methodology",
            "population",
            "seasonal_adjustment",
        ]
        assert metadata_gaps(report("r1")) == []


class TestDisplay:
    def test_one_report_is_one_card_with_no_range_or_band(self):
        display = build_display([report("r1")], [], [])
        assert [c.report_id for c in display.cards] == ["r1"]
        assert display.range is None and display.notes == []

    def test_two_comparable_independent_reports_give_a_labelled_range(self):
        reports = [report("r1", "4.9", "A"), report("r2", "5.25", "B")]
        display = build_display(reports, [member("r1"), member("r2")], [])
        assert display.range is not None
        assert (display.range.low, display.range.high, display.range.n) == ("4.9", "5.25", 2)
        assert display.range.label == "range of 2 reports; not a confidence interval"

    def test_the_range_uses_decimals_and_keeps_original_text(self):
        reports = [report("r1", "10.0", "A"), report("r2", "9.50", "B")]
        display = build_display(reports, [member("r1"), member("r2")], [])
        assert (display.range.low, display.range.high) == ("9.50", "10.0")

    def test_no_range_without_reviewer_assessment(self):
        display = build_display([report("r1", origin="A"), report("r2", "5", "B")], [], [])
        assert display.range is None
        assert any("not yet reviewed" in (c.difference or "") for c in display.cards)

    def test_an_unresolved_member_blocks_the_range(self):
        reports = [report("r1", origin="A"), report("r2", "5", "B")]
        display = build_display(
            reports, [member("r1"), member("r2", "unresolved", "scope unclear")], []
        )
        assert display.range is None

    def test_a_not_comparable_member_gets_a_difference_and_no_range(self):
        reports = [report("r1", origin="A"), report("r2", "5", "B")]
        memberships = [
            member("r1"),
            member("r2", "not_comparable", "covers only crude, not liquids"),
        ]
        display = build_display(reports, memberships, [])
        assert display.range is None
        card = next(c for c in display.cards if c.report_id == "r2")
        assert card.difference == "covers only crude, not liquids"

    def test_shared_origin_reports_do_not_form_a_range(self):
        reports = [report("r1", origin="A"), report("r2", "5", "A")]
        display = build_display(reports, [member("r1"), member("r2")], [])
        assert display.range is None
        assert any("origin" in n for n in display.notes)

    def test_a_declared_duplicate_origin_counts_once(self):
        reports = [report("r1", origin="A"), report("r2", "5", "B")]
        dup = Relation(
            left="r2",
            right="r1",
            relation="duplicates_origin",
            rationale="B repeats A",
            reviewer="Synthetic reviewer",
        )
        display = build_display(reports, [member("r1"), member("r2")], [dup])
        assert display.range is None

    def test_a_revision_hides_the_old_report_and_is_not_a_second_report(self):
        reports = [
            report("new", "5.0", "A"),
            report("old", "4.9", "A"),
            report("other", "5.2", "B"),
        ]
        rev = Relation(
            left="new",
            right="old",
            relation="revises",
            rationale="same series, later release",
            reviewer="Synthetic reviewer",
        )
        memberships = [member("new"), member("other")]
        display = build_display(reports, memberships, [rev])
        assert sorted(c.report_id for c in display.cards) == ["new", "other"]
        assert next(c for c in display.cards if c.report_id == "new").revised_from == ["old"]
        assert display.range.n == 2 and display.range.low == "5.0"

    def test_a_revision_alone_is_a_single_card_not_a_conflict(self):
        reports = [report("new", "5.0", "A"), report("old", "4.9", "A")]
        rev = Relation(
            left="new",
            right="old",
            relation="revises",
            rationale="later release",
            reviewer="Synthetic reviewer",
        )
        display = build_display(reports, [], [rev])
        assert [c.report_id for c in display.cards] == ["new"]
        assert display.range is None and display.notes == []

    def test_forecast_and_reported_never_share_a_range(self):
        reports = [report("r1", origin="A"), report("r2", "5", "B", epistemic_status="forecast")]
        display = build_display(reports, [member("r1"), member("r2")], [])
        assert display.range is None
        assert {c.lane for c in display.cards} == {"reported", "forecast"}

    def test_metadata_gaps_block_a_range(self):
        reports = [report("r1", origin="A"), report("r2", "5", "B", scope={})]
        display = build_display(reports, [member("r1"), member("r2")], [])
        assert display.range is None
        assert any("metadata" in n for n in display.notes)

    def test_different_units_never_share_a_range(self):
        reports = [report("r1", origin="A"), report("r2", "5", "B", unit_symbol="Mt")]
        display = build_display(reports, [member("r1"), member("r2")], [])
        assert display.range is None
