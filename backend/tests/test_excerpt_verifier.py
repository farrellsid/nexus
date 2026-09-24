"""The excerpt verifier decides whether a stored quote really appears in its cited page."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify_excerpts.py"


@pytest.fixture(scope="module")
def verifier():
    spec = importlib.util.spec_from_file_location("verify_excerpts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PAGE = """
<html><head><style>.x{color:red}</style><script>var hidden = "8.1 million";</script></head>
<body><h1>China&rsquo;s imports</h1>
<p>China imported just <b>8.1</b> million barrels per day (b/d) of crude oil in 2Q26,
32% less than the previous quarter.</p></body></html>
"""


class TestPageText:
    def test_markup_scripts_and_styles_are_removed(self, verifier):
        text = verifier.page_text(PAGE)
        assert "color:red" not in text
        assert "hidden" not in text
        assert "8.1 million barrels per day (b/d) of crude oil" in text

    def test_entities_quotes_dashes_and_spaces_are_normalised(self, verifier):
        text = verifier.page_text("<p>A – B “quoted”  and&nbsp;more</p>")
        assert text == 'a - b "quoted" and more'


class TestSpanExtraction:
    def test_the_original_case_of_a_span_can_be_recovered_for_storing(self, verifier):
        span = verifier.original_span(PAGE, "china imported just 8.1 million barrels per day (b/d)")
        assert span == "China imported just 8.1 million barrels per day (b/d)"

    def test_a_missing_span_returns_nothing(self, verifier):
        assert verifier.original_span(PAGE, "not on the page") is None


class TestFindExcerpt:
    def test_a_verbatim_quote_is_found_across_markup_and_line_breaks(self, verifier):
        assert verifier.find_excerpt(PAGE, "China imported just 8.1 million barrels per day")

    def test_a_dropped_parenthetical_is_not_verbatim(self, verifier):
        quote = "China imported just 8.1 million barrels per day of crude oil in 2Q26"
        assert not verifier.find_excerpt(PAGE, quote)

    def test_an_expanded_abbreviation_is_not_verbatim(self, verifier):
        assert not verifier.find_excerpt(
            "<p>averaged 13.7 million b/d</p>", "averaged 13.7 million barrels per day"
        )

    def test_trailing_punctuation_on_the_quote_is_tolerated(self, verifier):
        assert verifier.find_excerpt(
            "<p>Stocks fell 6.1 million barrels to 412.1 million barrels.</p>",
            "Stocks fell 6.1 million barrels to 412.1 million barrels—",
        )

    def test_an_empty_quote_is_never_found(self, verifier):
        assert not verifier.find_excerpt(PAGE, "  ")


class TestPdfDetection:
    @pytest.mark.parametrize(
        ("url", "content_type", "head", "expected"),
        [
            ("https://x.org/report.pdf", "text/html", b"<html", True),
            ("https://x.org/download.php?file=a.pdf", "application/pdf", b"%PDF-", True),
            ("https://x.org/download.php?file=a", "application/octet-stream", b"%PDF-1.7", True),
            ("https://x.org/page", "text/html; charset=utf-8", b"<!DOC", False),
        ],
    )
    def test_a_pdf_is_recognised_by_url_header_or_bytes(
        self, verifier, url, content_type, head, expected
    ):
        assert verifier.looks_like_pdf(url, content_type, head) is expected


class TestClassify:
    def test_a_found_quote_is_verbatim(self, verifier):
        assert (
            verifier.classify(PAGE, "China imported just 8.1 million barrels per day") == "verbatim"
        )

    def test_a_readable_page_without_the_quote_has_changed(self, verifier):
        long_page = "<p>" + "unrelated words " * 60 + "</p>"
        assert verifier.classify(long_page, "China imported just 8.1 million") == "changed"

    def test_a_page_with_almost_no_text_is_unreadable_not_changed(self, verifier):
        assert (
            verifier.classify("<html><script>app()</script><body></body></html>", "anything at all")
            == "unreadable"
        )


class TestKnownExceptions:
    def test_a_declared_exception_that_still_holds_is_accepted(self, verifier):
        assert (
            verifier.judge("unreadable", {"status": "unreadable", "reason": "script-rendered"})
            == "ok-exception"
        )

    def test_a_verbatim_source_needs_no_exception(self, verifier):
        assert verifier.judge("verbatim", None) == "ok"

    def test_an_undeclared_problem_fails(self, verifier):
        assert verifier.judge("changed", None) == "fail"

    def test_an_exception_that_no_longer_matches_fails(self, verifier):
        assert verifier.judge("changed", {"status": "unreadable", "reason": "x"}) == "fail"

    def test_an_exception_for_a_now_verbatim_source_is_flagged_as_stale(self, verifier):
        assert (
            verifier.judge("verbatim", {"status": "unreadable", "reason": "x"}) == "stale-exception"
        )


class TestFigureSupport:
    def test_a_figure_missing_from_every_cited_excerpt_is_reported(self, verifier):
        statement = "IEA estimated Iraqi crude oil production at 3.86 million b/d in August 2026."
        excerpts = ["Global oil production fell by 1.6 mb/d m-o-m to 100.1 mb/d in August."]
        assert verifier.unsupported_figures(statement, excerpts) == ["3.86"]

    def test_figures_present_in_any_cited_excerpt_are_supported(self, verifier):
        statement = "EIA estimated crude production at 13.7 million b/d, and 48% of imports."
        excerpts = ["averaged 13.7 million b/d", "accounted for 48% of the import volumes"]
        assert verifier.unsupported_figures(statement, excerpts) == []

    def test_dates_and_bare_years_are_not_treated_as_figures(self, verifier):
        assert (
            verifier.unsupported_figures(
                "Reported in April 2026 for 2026-Q2 on 2026-09-10.", ["nothing"]
            )
            == []
        )
