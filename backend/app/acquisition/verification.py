"""Three-state verification against a named baseline: matches, changed, unreachable.

These are comparisons, not truth scores. A raw-byte match and a text match are reported separately,
and passage support is reported separately from content drift. A missing baseline is never a match.
"""

from typing import Literal

from app.acquisition.extraction import TextExtraction, find_passage
from app.knowledge import Record

FAILED_FETCH = {"network_error", "access_denied", "blocked_target", "too_large", "http_error"}


class Baseline(Record):
    sha256: str
    text_sha256: str | None
    basis: str  # why this is the baseline; a first snapshot is a new baseline, not the original


class Attempt(Record):
    outcome: str
    sha256: str | None
    extraction: TextExtraction | None
    media_type: str | None


class PassageCheck(Record):
    phrase: str
    found: bool


class Verification(Record):
    state: Literal["matches", "changed", "unreachable"]
    reason: str
    comparison_readiness: Literal["ready", "not_ready"]
    byte_match: bool | None
    text_match: bool | None
    passages: list[PassageCheck]


def _unreachable(reason: str) -> Verification:
    return Verification(
        state="unreachable",
        reason=reason,
        comparison_readiness="not_ready",
        byte_match=None,
        text_match=None,
        passages=[],
    )


def verify(baseline: Baseline | None, attempt: Attempt, phrases: list[str]) -> Verification:
    if baseline is None:
        return _unreachable("baseline_missing")
    if attempt.outcome in FAILED_FETCH:
        return _unreachable(attempt.outcome)
    media = (attempt.media_type or "").lower()
    if not ("html" in media or "json" in media) or attempt.extraction is None:
        return _unreachable("unsupported_format")
    if not attempt.extraction.readable:
        return _unreachable("render_failed")

    byte_match = attempt.sha256 == baseline.sha256
    text_match = attempt.extraction.text_sha256 == baseline.text_sha256
    passages = [
        PassageCheck(phrase=phrase, found=find_passage(attempt.extraction.text, phrase) is not None)
        for phrase in phrases
    ]
    if byte_match:
        state, reason = "matches", "the response bytes equal the baseline"
    elif text_match:
        state, reason = "matches", "the extracted text equals the baseline; the bytes differ"
    else:
        state, reason = "changed", "the extracted text differs from the baseline"
    return Verification(
        state=state,
        reason=reason,
        comparison_readiness="ready",
        byte_match=byte_match,
        text_match=text_match,
        passages=passages,
    )
