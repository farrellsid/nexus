"""Figure extraction and the eval-case schema. Synthetic test data only."""

import pytest

from app.evaluation.cases import EvalCase, EvalSuite, validate_suite
from app.evaluation.figures import figures_in, unsupported


class TestFigures:
    def test_decimals_percentages_and_scaled_integers_are_figures(self):
        text = "Iraq 3.86 million b/d in 2026-Q2, 7% below, 1,234 barrels and 5 million"
        assert figures_in(text) == ["3.86", "7", "1,234", "5"]

    def test_dates_periods_and_bare_years_are_not_figures(self):
        assert figures_in("Reported 2026-09-11 for 2026-Q2 and 2025, in 1H25") == []

    def test_a_supported_figure_is_not_reported(self):
        assert unsupported("Iraq made 3.86 million b/d", ["IEA put Iraq at 3.86"]) == []

    def test_an_unsupported_figure_is_reported_once(self):
        assert unsupported("3.86 and 9.99 and 9.99", ["Iraq at 3.86"]) == ["9.99"]

    def test_thousands_separators_are_ignored_when_matching(self):
        assert unsupported("1,234 barrels", ["stocks were 1234 barrels"]) == []

    def test_a_percentage_is_supported_by_the_same_number_in_the_source(self):
        assert unsupported("7% below the average", ["stocks 7% below the five-year average"]) == []


def case(**changes):
    base = {
        "id": "Q1",
        "answer_class": "supported",
        "required_claims": ["C1"],
        "required_measurements": [],
        "required_sources": [],
        "context_claims": [],
        "required_qualifiers": [],
        "prohibited_assertions": [],
        "expected_entities": [],
        "oracle_review_status": "assistant_draft",
        "split": "development",
        "notes": "",
    }
    return EvalCase(**{**base, **changes})


def problems(cases, acceptance=("Q1",)):
    suite = EvalSuite(suite_id="s", version="1", release_id="r", cases=cases)
    return validate_suite(
        suite,
        acceptance_ids=set(acceptance),
        claim_ids={"C1", "C2"},
        measurement_ids={"M:1"},
        source_ids={"S1"},
        entity_ids={"place/x"},
    )


def test_a_correct_suite_has_no_problems():
    assert problems([case()]) == []


def test_an_acceptance_case_without_an_eval_case_is_reported():
    assert any("missing" in p and "Q2" in p for p in problems([case()], acceptance=("Q1", "Q2")))


def test_an_eval_case_for_an_unknown_acceptance_id_is_reported():
    assert any("unknown" in p and "Q9" in p for p in problems([case(), case(id="Q9")]))


def test_a_duplicate_case_is_reported():
    assert any("twice" in p and "Q1" in p for p in problems([case(), case()]))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("required_claims", ["C9"]),
        ("required_measurements", ["M:9"]),
        ("required_sources", ["S9"]),
        ("context_claims", ["C9"]),
        ("expected_entities", ["place/nope"]),
    ],
)
def test_an_unresolved_reference_is_reported(field, value):
    assert any(value[0] in p for p in problems([case(**{field: value})]))


def test_a_supported_case_needs_required_facts():
    assert any("supported" in p for p in problems([case(required_claims=[])]))


def test_an_unknown_case_may_not_require_facts():
    found = problems([case(answer_class="unknown", required_claims=["C1"])])
    assert any("unknown" in p and "required" in p for p in found)


def test_an_unknown_case_may_list_context():
    assert problems([case(answer_class="unknown", required_claims=[], context_claims=["C2"])]) == []


def test_a_partial_case_needs_a_required_qualifier():
    assert any("partial" in p for p in problems([case(answer_class="partial")]))
    assert problems([case(answer_class="partial", required_qualifiers=["revision-prone"])]) == []
