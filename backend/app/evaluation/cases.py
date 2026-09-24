"""Evaluation cases: what a correct answer to each authored question must rest on.

Expected answers in the acceptance records are drafts of an oracle, not ground truth. A case
names the records an answer needs, the qualifiers it must keep and the assertions it must not make.
"""

from collections import Counter
from typing import Literal

from app.knowledge import Record


class EvalCase(Record):
    id: str  # the acceptance record's ID
    answer_class: Literal["supported", "partial", "unknown"]
    required_claims: list[str]
    required_measurements: list[str]
    required_sources: list[str]
    context_claims: list[str]  # relevant to the question but not permitted as answer facts
    required_qualifiers: list[str]
    prohibited_assertions: list[str]
    expected_entities: list[str]
    oracle_review_status: Literal["assistant_draft", "user_confirmed"]
    split: Literal["development", "held_out"]
    notes: str


class EvalSuite(Record):
    suite_id: str
    version: str
    release_id: str  # the accepted normalisation release the entity IDs come from
    cases: list[EvalCase]


def validate_suite(
    suite: EvalSuite,
    acceptance_ids: set[str],
    claim_ids: set[str],
    measurement_ids: set[str],
    source_ids: set[str],
    entity_ids: set[str],
) -> list[str]:
    """Return every problem found; an empty list means the suite is consistent."""
    problems = [
        f"case {k} appears twice" for k, n in Counter(c.id for c in suite.cases).items() if n > 1
    ]
    listed = {c.id for c in suite.cases}
    problems += [f"missing case for acceptance record {i}" for i in sorted(acceptance_ids - listed)]
    problems += [f"unknown acceptance record {i}" for i in sorted(listed - acceptance_ids)]
    for case in suite.cases:
        for field, known in (
            ("required_claims", claim_ids),
            ("context_claims", claim_ids),
            ("required_measurements", measurement_ids),
            ("required_sources", source_ids),
            ("expected_entities", entity_ids),
        ):
            problems += [
                f"case {case.id} {field} {ref} does not resolve"
                for ref in getattr(case, field)
                if ref not in known
            ]
        has_facts = bool(case.required_claims or case.required_measurements)
        if case.answer_class == "supported" and not has_facts:
            problems.append(f"case {case.id} is supported but requires no claim or measurement")
        if case.answer_class == "unknown" and has_facts:
            problems.append(
                f"case {case.id} is unknown but lists required facts; use context_claims"
            )
        if case.answer_class == "partial" and not case.required_qualifiers:
            problems.append(f"case {case.id} is partial but requires no qualifier")
    return problems
