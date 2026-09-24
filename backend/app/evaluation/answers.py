"""The structured answer contract and its checker.

An answerer receives only the question and the retrieved hits. The checker holds the oracle
(the eval case) and reports every rule a candidate answer breaks; it cannot prove entailment,
so free prose still needs human review.
"""

from app.evaluation.cases import EvalCase
from app.evaluation.corpus import Corpus
from app.evaluation.figures import unsupported
from app.evaluation.retrieval import Hit
from app.knowledge import Record


class Fact(Record):
    text: str
    cites: list[str]


class Answer(Record):
    abstained: bool
    facts: list[Fact]
    limitation: str = ""


class AlwaysAbstain:
    """The baseline: proves the harness scores something and that unknown cases can be passed."""

    def answer(self, question: str, hits: list[Hit]) -> Answer:
        return Answer(abstained=True, facts=[], limitation="Not answered by the baseline.")


def check_answer(case: EvalCase, answer: Answer, corpus: Corpus) -> list[str]:
    """Return every violation; an empty list means the answer meets the case's contract."""
    violations: list[str] = []
    texts = {record.ref: record.text for record in corpus.records}
    required = [f"claim:{c}" for c in case.required_claims]
    required += [f"measurement:{m}" for m in case.required_measurements]

    if answer.abstained:
        if required and case.answer_class != "unknown":
            violations.append(f"case {case.id}: abstained although the corpus supports an answer")
    elif case.answer_class == "unknown":
        violations.append(f"case {case.id}: is unknown, so the answer must abstain")

    cited = {ref for fact in answer.facts for ref in fact.cites}
    violations += [
        f"case {case.id}: citation {ref} does not resolve" for ref in sorted(cited - texts.keys())
    ]
    violations += [
        f"case {case.id}: required record {ref} is not cited"
        for ref in required
        if ref not in cited
    ]
    for fact in answer.facts:
        support = [texts[ref] for ref in fact.cites if ref in texts]
        violations += [
            f"case {case.id}: figure {figure} is not in its cited records"
            for figure in unsupported(fact.text, support)
        ]
    prose = " ".join([*(fact.text for fact in answer.facts), answer.limitation]).lower()
    violations += [
        f"case {case.id}: prohibited assertion {phrase!r}"
        for phrase in case.prohibited_assertions
        if phrase.lower() in prose
    ]
    violations += [
        f"case {case.id}: required qualifier {phrase!r} is missing"
        for phrase in case.required_qualifiers
        if phrase.lower() not in prose
    ]
    return violations
