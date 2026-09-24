"""Extraction is deterministic and keeps the page's own characters. Synthetic test data."""

from app.acquisition.extraction import EXTRACTOR, extract_text, find_passage

LONG = "<p>" + "Filler words for length. " * 12 + "</p>"
PAGE = f"""
<html><head><title>T</title><style>.x{{color:red}}</style>
<script>var hidden = "9.99 million";</script></head>
<body><h1>China’s imports</h1>
{LONG}
<p>China imported just <b>8.1</b> million barrels per day (b/d) of crude<br>oil in 2Q26 –
about 32% less.</p>
<table><tr><td>Iraq</td><td>3.86</td></tr><tr><td>Russia<sup>1</sup></td><td>8.36</td></tr></table>
</body></html>
"""


def test_the_same_markup_always_gives_the_same_hash():
    first, second = extract_text(PAGE), extract_text(PAGE)
    assert first == second and first.extractor == EXTRACTOR
    assert len(first.text_sha256) == 64


def test_whitespace_only_differences_give_the_same_hash():
    squeezed = PAGE.replace("\n", " ").replace("  ", " ")
    assert extract_text(squeezed).text_sha256 == extract_text(PAGE).text_sha256


def test_scripts_and_styles_are_excluded():
    text = extract_text(PAGE).text
    assert "9.99" not in text and "color:red" not in text


def test_block_tags_separate_words_but_inline_markers_do_not():
    text = extract_text(PAGE).text
    assert "crude oil in 2Q26" in text
    assert "Iraq 3.86" in text
    assert "Russia1 8.36" in text


def test_case_quotes_and_dashes_are_preserved():
    text = extract_text(PAGE).text
    assert "China’s imports" in text and "2Q26 – about" in text


def test_a_page_with_almost_no_text_is_not_readable():
    shell = extract_text("<html><body><div id='app'></div><script>boot()</script></body></html>")
    assert shell.readable is False
    assert extract_text(PAGE).readable is True


def test_a_passage_is_found_with_its_exact_span():
    extraction = extract_text(PAGE)
    phrase = "China imported just 8.1 million barrels per day (b/d)"
    passage = find_passage(extraction.text, phrase)
    assert passage.text == phrase
    assert extraction.text[passage.start : passage.end] == phrase


def test_a_passage_spanning_a_line_break_is_found():
    extraction = extract_text(PAGE)
    assert find_passage(extraction.text, "crude\n  oil in 2Q26") is not None


def test_a_passage_with_a_different_dash_or_case_is_not_found():
    text = extract_text(PAGE).text
    assert find_passage(text, "2Q26 - about 32% less") is None  # hyphen, not the page's en dash
    assert find_passage(text, "china imported just 8.1") is None  # case differs
    assert find_passage(text, "not on the page") is None


class TestJsonRows:
    BODY = (
        '{"response":{"total":"2","data":['
        '{"period":"2026-06-19","duoarea":"NUS","area-name":"U.S.","series":"WCESTUS1",'
        '"series-description":"U.S. Ending Stocks","value":"412134","units":"MBBL"},'
        '{"period":"2026-06-26","duoarea":"NUS","area-name":"U.S.","series":"WCESTUS1",'
        '"series-description":"U.S. Ending Stocks","value":"408359","units":"MBBL"}'
        ']},"request":{"command":"/v2/x"},"apiVersion":"2.1.11"}'
    )

    def test_rows_become_compact_canonical_text_without_descriptive_fields(self):
        from app.acquisition.extraction import JSON_EXTRACTOR, extract_json_rows

        extraction = extract_json_rows(self.BODY)
        assert extraction.extractor == JSON_EXTRACTOR and extraction.readable
        assert extraction.text == (
            '[{"duoarea":"NUS","period":"2026-06-19","series":"WCESTUS1","units":"MBBL",'
            '"value":"412134"},{"duoarea":"NUS","period":"2026-06-26","series":"WCESTUS1",'
            '"units":"MBBL","value":"408359"}]'
        )

    def test_volatile_response_metadata_does_not_change_the_hash(self):
        from app.acquisition.extraction import extract_json_rows

        other = self.BODY.replace("2.1.11", "2.1.12").replace('"/v2/x"', '"/v2/y"')
        assert extract_json_rows(other).text_sha256 == extract_json_rows(self.BODY).text_sha256

    def test_a_row_changing_its_value_changes_the_hash(self):
        from app.acquisition.extraction import extract_json_rows

        other = self.BODY.replace("412134", "412135")
        assert extract_json_rows(other).text_sha256 != extract_json_rows(self.BODY).text_sha256

    def test_a_passage_is_an_exact_row_span(self):
        from app.acquisition.extraction import extract_json_rows, find_passage

        text = extract_json_rows(self.BODY).text
        row = (
            '{"duoarea":"NUS","period":"2026-06-19","series":"WCESTUS1",'
            '"units":"MBBL","value":"412134"}'
        )
        assert find_passage(text, row) is not None

    def test_an_error_or_empty_document_is_not_readable(self):
        from app.acquisition.extraction import extract_json_rows

        assert extract_json_rows('{"error":{"code":"API_KEY_MISSING"}}').readable is False
        assert extract_json_rows('{"response":{"data":[]}}').readable is False
        assert extract_json_rows("not json").readable is False
