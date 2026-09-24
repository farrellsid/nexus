"""The oracle audit flags expected answers and records that their evidence does not support."""

from app.evaluation.cases import EvalCase
from app.evaluation.corpus import Corpus, CorpusRecord
from app.evaluation.oracle import oracle_findings

CORPUS = Corpus(
    records=[
        CorpusRecord(
            ref="claim:C1",
            kind="claim",
            text="EIA estimated flows at 4.9 million b/d in 2026-Q2",
            entities=[],
            source_refs=["source:S1"],
        ),
        CorpusRecord(
            ref="measurement:M:1",
            kind="measurement",
            text="Hormuz flow 21.6 million barrels per day",
            entities=[],
            source_refs=["source:S1"],
        ),
        CorpusRecord(
            ref="source:S1",
            kind="source",
            text="Flows through Hormuz fell to 4.9 million b/d",
            entities=[],
        ),
    ],
    entity_names={},
)


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


def test_a_fully_supported_oracle_has_no_findings():
    assert oracle_findings(case(), CORPUS, "Flows fell to 4.9 million b/d.") == []


def test_a_figure_in_the_expected_answer_that_no_required_record_holds_is_flagged():
    found = oracle_findings(case(), CORPUS, "Flows fell to 9.99 million b/d.")
    assert any("9.99" in f and "expected answer" in f for f in found)


def test_a_required_record_whose_figure_its_sources_lack_is_flagged():
    found = oracle_findings(
        case(required_measurements=["M:1"]), CORPUS, "Flows were 21.6 million b/d."
    )
    assert any("measurement:M:1" in f and "21.6" in f and "cited sources" in f for f in found)


def test_context_records_may_support_the_expected_answer():
    unknown = case(answer_class="unknown", required_claims=[], context_claims=["C1"])
    assert (
        oracle_findings(unknown, CORPUS, "Unknown, although 4.9 million b/d was estimated.") == []
    )
