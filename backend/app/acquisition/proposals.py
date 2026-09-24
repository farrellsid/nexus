"""Mechanical gates for a proposed piece of evidence.

The gates reject what code can check: unknown sources, quotations that are not on the page, figures
that are absent or bound to the wrong row or position, missing units and periods, plans stated as
facts. A proposal that passes may enter human review; passing never means the claim is entailed.
Page text is data: nothing in it can change a gate's outcome.
"""

import re
from typing import Literal

from app.acquisition.extraction import TextExtraction, find_passage
from app.evaluation.figures import DATE_LIKE, unsupported
from app.knowledge import Record

PLAN_MARKERS = (
    "expected", "expects", "planned", "plans", "forecast", "will", "would", "could",
    "may", "scheduled", "anticipated", "projected",
)  # fmt: skip
QUOTES = ('"', "“", "”")
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


class ExtractionProposal(Record):
    source_id: str
    passage_kind: Literal["verbatim", "ocr_transcription", "authored_summary"]
    excerpt: str
    locator: str
    claim_statement: str
    figures: list[str]
    entity: str | None = None  # the row or subject the figure belongs to
    figure_position: int = 1  # the figure is the Nth number after the entity in the excerpt
    unit: str | None = None
    period: str | None = None
    review_step: str | None = None  # required for an OCR transcription


def _has_marker(text: str) -> bool:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return any(marker in words for marker in PLAN_MARKERS)


def _numbers_after(excerpt: str, entity: str) -> list[str] | None:
    start = excerpt.find(entity)
    if start < 0:
        return None
    after = DATE_LIKE.sub(" ", excerpt[start + len(entity) :])
    return [token.replace(",", "").rstrip(".") for token in NUMBER.findall(after)]


def gate_proposal(
    proposal: ExtractionProposal, extraction: TextExtraction, known_source_ids: set[str]
) -> list[str]:
    """Return every reason to reject; an empty list means the proposal may enter review."""
    reasons: list[str] = []
    if proposal.source_id not in known_source_ids:
        reasons.append(f"unknown source {proposal.source_id}")
    if not proposal.locator.strip():
        reasons.append("a locator is required")
    if not extraction.readable:
        reasons.append("the extraction is not readable, so nothing can be located")
        return reasons

    excerpt = proposal.excerpt
    if proposal.passage_kind == "verbatim" and find_passage(extraction.text, excerpt) is None:
        reasons.append("the excerpt is not an exact span of the extracted page text")
    if proposal.passage_kind == "authored_summary" and any(mark in excerpt for mark in QUOTES):
        reasons.append("an authored summary must not carry quotation marks")
    if proposal.passage_kind == "ocr_transcription" and not (proposal.review_step or "").strip():
        reasons.append("an OCR transcription needs a stated human review step")

    reasons += [
        f"statement figure {figure} is not in the excerpt"
        for figure in unsupported(proposal.claim_statement, [excerpt])
    ]
    present = {token.replace(",", "") for token in NUMBER.findall(excerpt)}
    reasons += [
        f"declared figure {figure} is not in the excerpt"
        for figure in proposal.figures
        if figure.replace(",", "") not in present
    ]
    if proposal.entity and proposal.figures:
        numbers = _numbers_after(excerpt, proposal.entity)
        for figure in proposal.figures:
            wanted = figure.replace(",", "")
            if numbers is None:
                reasons.append(f"the entity {proposal.entity} is not in the excerpt")
            elif len(numbers) < proposal.figure_position:
                reasons.append(
                    f"{proposal.entity} has no number at position {proposal.figure_position}"
                )
            elif numbers[proposal.figure_position - 1] != wanted:
                found = numbers[proposal.figure_position - 1]
                reasons.append(
                    f"figure {figure} is not the number at position {proposal.figure_position} "
                    f"after {proposal.entity} (that is {found})"
                )
    if proposal.unit and proposal.unit.lower() not in excerpt.lower():
        reasons.append(f"the stated unit {proposal.unit!r} is not in the excerpt")
    if proposal.period and proposal.period.lower() not in excerpt.lower():
        reasons.append(f"the stated period {proposal.period!r} is not in the excerpt")
    if _has_marker(excerpt) and not _has_marker(proposal.claim_statement):
        reasons.append("the excerpt describes a plan or forecast but the statement reads as fact")
    return reasons
