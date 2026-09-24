"""Audit an eval case's oracle against its evidence.

Two checks, both figure-based and so necessary but not sufficient: the expected answer's figures
must appear in the records the case requires, and each required record's own figures must appear
in the sources it cites. A finding is a prompt for human review, never proof of an error.
"""

from app.evaluation.cases import EvalCase
from app.evaluation.corpus import Corpus
from app.evaluation.figures import figures_in, unsupported


def oracle_findings(case: EvalCase, corpus: Corpus, expected_answer: str) -> list[str]:
    by_ref = {record.ref: record for record in corpus.records}
    facts = [f"claim:{c}" for c in case.required_claims]
    facts += [f"measurement:{m}" for m in case.required_measurements]
    context = [f"claim:{c}" for c in case.context_claims]
    sources = [f"source:{s}" for s in case.required_sources]

    support = [by_ref[ref].text for ref in (*facts, *context, *sources) if ref in by_ref]
    findings = [
        f"case {case.id}: expected answer figure {figure} is not in any required or context record"
        for figure in unsupported(expected_answer, support)
    ]
    for ref in facts:
        record = by_ref.get(ref)
        if record is None or not figures_in(record.text):
            continue
        cited = [by_ref[s].text for s in record.source_refs if s in by_ref]
        findings += [
            f"case {case.id}: {ref} figure {figure} is not in its cited sources"
            for figure in unsupported(record.text, cited)
        ]
    return findings
