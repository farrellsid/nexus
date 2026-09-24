"""Verification compares to a named baseline and never claims truth. Synthetic test data."""

import pytest

from app.acquisition.extraction import extract_text
from app.acquisition.verification import Attempt, Baseline, verify

BODY = (
    "<p>" + "Some stable page text for the fixture. " * 10 + "China imported 8.1 million b/d.</p>"
)
CHANGED = BODY.replace("8.1", "7.9")
PHRASE = "China imported 8.1 million b/d."


def attempt(markup=BODY, sha="sha-a", outcome="ok", media="text/html"):
    extraction = extract_text(markup) if outcome == "ok" else None
    return Attempt(
        outcome=outcome,
        sha256=sha if outcome == "ok" else None,
        extraction=extraction,
        media_type=media if outcome == "ok" else None,
    )


def baseline(markup=BODY, sha="sha-a"):
    return Baseline(
        sha256=sha, text_sha256=extract_text(markup).text_sha256, basis="first snapshot"
    )


def test_equal_bytes_match():
    result = verify(baseline(), attempt(), [PHRASE])
    assert (result.state, result.byte_match, result.text_match) == ("matches", True, True)
    assert result.comparison_readiness == "ready"
    assert [(p.phrase, p.found) for p in result.passages] == [(PHRASE, True)]


def test_equal_text_with_different_bytes_still_matches_and_says_which():
    noisy = BODY + "<!-- build 4711 -->"
    result = verify(baseline(), attempt(noisy, sha="sha-b"), [PHRASE])
    assert (result.state, result.byte_match, result.text_match) == ("matches", False, True)
    assert "text" in result.reason


def test_changed_text_is_changed_and_passage_support_is_reported_separately():
    result = verify(baseline(), attempt(CHANGED, sha="sha-b"), [PHRASE, "Some stable page text"])
    assert result.state == "changed"
    assert [p.found for p in result.passages] == [False, True]


def test_a_byte_change_with_every_passage_still_present_is_drift_not_a_failed_claim():
    drifted = BODY + "<p>New banner text added to the page.</p>"
    result = verify(baseline(), attempt(drifted, sha="sha-b"), [PHRASE])
    assert result.state == "changed" and all(p.found for p in result.passages)


def test_a_missing_baseline_is_never_a_match():
    result = verify(None, attempt(), [PHRASE])
    assert (result.state, result.reason) == ("unreachable", "baseline_missing")
    assert result.comparison_readiness == "not_ready"


@pytest.mark.parametrize(
    "outcome", ["network_error", "access_denied", "blocked_target", "too_large"]
)
def test_a_failed_fetch_is_unreachable_with_its_own_reason(outcome):
    result = verify(baseline(), attempt(outcome=outcome), [PHRASE])
    assert (result.state, result.reason) == ("unreachable", outcome)
    assert result.comparison_readiness == "not_ready"
    assert result.byte_match is None and result.text_match is None


def test_a_non_html_response_is_an_unsupported_format():
    pdf = Attempt(outcome="ok", sha256="sha-a", extraction=None, media_type="application/pdf")
    result = verify(baseline(), pdf, [PHRASE])
    assert (result.state, result.reason) == ("unreachable", "unsupported_format")


def test_a_shell_page_is_a_render_failure_not_a_match():
    shell = attempt("<html><body><div id='app'></div></body></html>", sha="sha-a")
    result = verify(baseline(), shell, [PHRASE])
    assert (result.state, result.reason) == ("unreachable", "render_failed")


def test_reasons_never_say_the_site_is_offline():
    reasons = [
        verify(None, attempt(), []).reason,
        verify(baseline(), attempt(outcome="network_error"), []).reason,
    ]
    assert not any("offline" in reason for reason in reasons)


def test_a_json_response_can_be_verified_like_a_page():
    from app.acquisition.extraction import extract_json_rows

    body = (
        '{"response":{"data":[{"period":"2026-06-19","series":"S",'
        '"value":"412134","units":"MBBL"}]}}'
    )
    extraction = extract_json_rows(body)
    row = '{"period":"2026-06-19","series":"S","units":"MBBL","value":"412134"}'
    baseline = Baseline(sha256="a", text_sha256=extraction.text_sha256, basis="first snapshot")
    attempt = Attempt(
        outcome="ok", sha256="b", extraction=extraction, media_type="application/json"
    )
    result = verify(baseline, attempt, [row])
    assert (result.state, result.text_match) == ("matches", True)
    assert result.passages[0].found is True
