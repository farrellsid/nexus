"""A deterministic lexical retriever (BM25 plus an entity boost) and its scoring.

The retriever sees only the question and the corpus, never an eval case. Ties break by reference.
"""

import math
import re
from collections import Counter

from app.evaluation.cases import EvalCase
from app.evaluation.corpus import Corpus
from app.knowledge import Record

K1, B, ENTITY_BOOST = 1.5, 0.75, 2.0
STOP_WORDS = frozenset(
    "a an and are as at be by did do does for from how in is it of on or that the this to was "
    "were what which who why with".split()
)


class Hit(Record):
    ref: str
    score: float


class RetrievalScore(Record):
    found: list[str]
    missing: list[str]
    recall: tuple[int, int]
    first_relevant_rank: int | None
    full_support: bool
    sources_found: list[str]
    sources_missing: list[str]


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())
    return [word for word in words if word not in STOP_WORDS]


def retrieve(corpus: Corpus, question: str, k: int = 10) -> list[Hit]:
    query = tokens(question)
    documents = [Counter(tokens(record.text)) for record in corpus.records]
    lengths = [sum(document.values()) for document in documents]
    average = (sum(lengths) / len(lengths)) if lengths else 1.0
    total = len(documents)
    lowered = question.lower()
    named = {
        entity
        for entity, names in corpus.entity_names.items()
        if any(name.lower() in lowered for name in names)
    }
    hits: list[Hit] = []
    for record, document, length in zip(corpus.records, documents, lengths, strict=True):
        score = 0.0
        for term in set(query):
            frequency = document.get(term, 0)
            if not frequency:
                continue
            containing = sum(1 for other in documents if term in other)
            idf = math.log(1 + (total - containing + 0.5) / (containing + 0.5))
            score += idf * frequency * (K1 + 1) / (frequency + K1 * (1 - B + B * length / average))
        if named & set(record.entities):
            score += ENTITY_BOOST
        if score > 0:
            hits.append(Hit(ref=record.ref, score=round(score, 6)))
    hits.sort(key=lambda hit: (-hit.score, hit.ref))
    return hits[:k]


def score_retrieval(case: EvalCase, hits: list[Hit], k: int) -> RetrievalScore:
    """Compare the top-k hits with the records the case requires."""
    top = [hit.ref for hit in hits[:k]]
    facts = [f"claim:{c}" for c in case.required_claims]
    facts += [f"measurement:{m}" for m in case.required_measurements]
    sources = [f"source:{s}" for s in case.required_sources]
    found = [ref for ref in facts if ref in top]
    relevant = set(facts) | set(sources)
    rank = next((i + 1 for i, ref in enumerate(top) if ref in relevant), None)
    return RetrievalScore(
        found=found,
        missing=[ref for ref in facts if ref not in top],
        recall=(len(found), len(facts)),
        first_relevant_rank=rank,
        full_support=len(found) == len(facts),
        sources_found=[ref for ref in sources if ref in top],
        sources_missing=[ref for ref in sources if ref not in top],
    )
