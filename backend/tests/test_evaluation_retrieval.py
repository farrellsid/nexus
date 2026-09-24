"""The lexical retriever is deterministic and never sees expected answers. Synthetic test data."""

from app.evaluation.cases import EvalCase
from app.evaluation.corpus import Corpus, CorpusRecord
from app.evaluation.retrieval import retrieve, score_retrieval


def rec(ref, text, entities=()):
    kind = ref.split(":", 1)[0]
    return CorpusRecord(ref=ref, kind=kind, text=text, entities=list(entities))


CORPUS = Corpus(
    records=[
        rec("claim:C1", "Strait of Hormuz oil flows fell in the second quarter", ["place/hormuz"]),
        rec("claim:C2", "Pipeline capacity bypasses the strait", ["infra/pipeline"]),
        rec("claim:C3", "Refinery utilization rose in September", ["place/us"]),
        rec("measurement:M:1", "Hormuz oil flow 4.9 million barrels per day", ["place/hormuz"]),
        rec("source:S1", "EIA report about weather and unrelated matters", []),
    ],
    entity_names={"place/hormuz": ["Strait of Hormuz"], "place/us": ["United States"]},
)


def test_the_record_matching_the_most_query_terms_ranks_first():
    hits = retrieve(CORPUS, "What happened to oil flows through Hormuz?", k=3)
    assert hits[0].ref in {"claim:C1", "measurement:M:1"}
    assert "claim:C3" not in [h.ref for h in hits[:2]]


def test_retrieval_is_deterministic():
    question = "What happened to oil flows through Hormuz?"
    assert retrieve(CORPUS, question, k=5) == retrieve(CORPUS, question, k=5)


def test_equal_scores_are_ordered_by_reference():
    tied = Corpus(
        records=[rec("claim:B", "same words here"), rec("claim:A", "same words here")],
        entity_names={},
    )
    assert [h.ref for h in retrieve(tied, "same words", k=2)] == ["claim:A", "claim:B"]


def test_a_named_entity_lifts_records_that_carry_it():
    plain = retrieve(CORPUS, "utilization", k=1)
    assert plain[0].ref == "claim:C3"
    boosted = retrieve(CORPUS, "What about the United States?", k=1)
    assert boosted[0].ref == "claim:C3"


def test_records_with_no_matching_terms_are_not_returned():
    assert retrieve(CORPUS, "zebra", k=5) == []


def test_k_limits_the_number_of_hits():
    assert len(retrieve(CORPUS, "oil flows strait pipeline capacity", k=2)) == 2


def case(**changes):
    base = {
        "id": "Q1",
        "answer_class": "supported",
        "required_claims": ["C1"],
        "required_measurements": ["M:1"],
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


def test_scoring_reports_found_and_missing_records():
    hits = retrieve(CORPUS, "Hormuz oil flow", k=1)
    score = score_retrieval(case(required_measurements=["M:1"]), hits, k=1)
    assert score.recall[1] == 2
    assert score.recall[0] == len(score.found)
    assert set(score.found) | set(score.missing) == {"claim:C1", "measurement:M:1"}
    assert score.full_support is (not score.missing)


def test_full_support_needs_everything_and_reports_the_first_relevant_rank():
    hits = retrieve(CORPUS, "Hormuz oil flow million barrels", k=5)
    score = score_retrieval(case(), hits, k=5)
    assert score.full_support
    assert score.first_relevant_rank == 1


def test_a_case_with_nothing_required_is_trivially_supported():
    score = score_retrieval(
        case(answer_class="unknown", required_claims=[], required_measurements=[]), [], k=5
    )
    assert score.recall == (0, 0)
    assert score.full_support
    assert score.first_relevant_rank is None


def test_a_measurement_record_lists_its_bound_sources_as_backing_sources():
    import json
    from pathlib import Path

    from app.evaluation.corpus import build_corpus
    from app.investigation import load_investigations
    from app.main import INVESTIGATIONS
    from app.normalisation.release import Release

    root = Path(__file__).resolve().parents[2]
    release = Release.model_validate_json(
        (root / "normalisation/releases/2026-09-24-r3.json").read_text("utf-8")
    )
    corpus = build_corpus(load_investigations(INVESTIGATIONS), release)
    stocks = next(r for r in corpus.records if r.ref.endswith(":O-M07:2"))
    assert stocks.source_refs[-1] == "source:O-S28" and "source:O-S14" in stocks.source_refs
    unbound = next(r for r in corpus.records if r.ref.endswith(":O-M01:3"))
    assert unbound.source_refs == ["source:O-S01"]
    assert json.dumps(stocks.source_refs)  # serialisable
