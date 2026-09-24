"""Evaluate the authored questions without any model: validate, retrieve, check, audit.

    python scripts/evaluate.py check          # validate the suite against the real packs
    python scripts/evaluate.py run --k 10     # retrieval raw counts and the abstain baseline
    python scripts/evaluate.py oracle         # expected answers against their evidence

Counts are raw. Failed cases are listed, never averaged. Run from `backend/` with
PYTHONPATH=. (as the other scripts). Nothing here writes to a database or calls a network.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "industry-v1" / "suite.json"
RELEASES = ROOT / "normalisation" / "releases"


def _load():
    from app.evaluation.cases import EvalSuite
    from app.evaluation.corpus import build_corpus
    from app.investigation import load_investigations
    from app.normalisation.release import Release

    suite = EvalSuite.model_validate_json(SUITE.read_text("utf-8"))
    release = next(
        release
        for release in (
            Release.model_validate_json(path.read_text("utf-8"))
            for path in sorted(RELEASES.glob("*.json"))
        )
        if release.release_id == suite.release_id
    )
    investigations = load_investigations(ROOT / "investigations")
    acceptance = {}
    for directory in sorted((ROOT / "investigations").iterdir()):
        path = directory / "acceptance-cases.json"
        if path.is_file():
            for record in json.loads(path.read_text("utf-8")):
                acceptance[record["id"]] = record
    return (
        suite,
        release,
        investigations,
        acceptance,
        build_corpus(investigations, release),
    )


def validate(suite, release, investigations, acceptance) -> list[str]:
    from app.evaluation.cases import validate_suite

    return validate_suite(
        suite,
        acceptance_ids=set(acceptance),
        claim_ids={c.id for i in investigations for c in i.pack.claims},
        measurement_ids={m.id for m in release.measurements},
        source_ids={s.id for i in investigations for s in i.pack.sources},
        entity_ids={e.canonical_id for e in release.entities},
    )


def _check() -> int:
    suite, release, investigations, acceptance, _ = _load()
    problems = validate(suite, release, investigations, acceptance)
    for problem in problems:
        print(f"PROBLEM  {problem}")
    confirmed = sum(c.oracle_review_status == "user_confirmed" for c in suite.cases)
    print(
        f"{suite.suite_id} v{suite.version}: {len(suite.cases)} cases, "
        f"{confirmed} oracle(s) confirmed by the user, {len(problems)} problem(s)"
    )
    return 1 if problems else 0


def _run(k: int) -> int:
    from app.evaluation.answers import AlwaysAbstain, check_answer
    from app.evaluation.retrieval import retrieve, score_retrieval

    suite, release, investigations, acceptance, corpus = _load()
    problems = validate(suite, release, investigations, acceptance)
    if problems:
        print("\n".join(f"PROBLEM  {p}" for p in problems))
        return 1
    print(f"retrieval at k={k}; baseline = always abstain\n")
    print(f"{'case':7}{'class':10}{'facts':7}{'full':6}{'rank':6}{'sources':9}baseline")
    full = passed = 0
    supported = 0
    failures = []
    for case in suite.cases:
        question = acceptance[case.id]["question"]
        hits = retrieve(corpus, question, k)
        score = score_retrieval(case, hits, k)
        answer = AlwaysAbstain().answer(question, hits)
        violations = check_answer(case, answer, corpus)
        needs = bool(case.required_claims or case.required_measurements)
        full += needs and score.full_support
        supported += needs
        passed += not violations
        if needs and not score.full_support:
            failures.append((case.id, score.missing))
        wanted = len(score.sources_found) + len(score.sources_missing)
        sources = f"{len(score.sources_found)}/{wanted}"
        rank = score.first_relevant_rank or "-"
        found = f"{score.recall[0]}/{score.recall[1]}"
        verdict = "pass" if not violations else f"{len(violations)} violation(s)"
        print(
            f"{case.id:7}{case.answer_class:10}{found:7}{score.full_support!s:6}"
            f"{rank!s:6}{sources:9}{verdict}"
        )
    print(f"\nfull support: {full} of {supported} cases that need facts")
    print(f"baseline meets the contract: {passed} of {len(suite.cases)} cases")
    for case_id, missing in failures:
        print(f"  {case_id} missing {', '.join(missing)}")
    return 0


def _oracle() -> int:
    from app.evaluation.oracle import oracle_findings

    suite, _, _, acceptance, corpus = _load()
    total = 0
    for case in suite.cases:
        for finding in oracle_findings(
            case, corpus, acceptance[case.id]["expected_answer"]
        ):
            print(finding)
            total += 1
    print(
        f"\n{total} finding(s) across {len(suite.cases)} cases (prompts for review, not proof)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    run = commands.add_parser("run")
    run.add_argument("--k", type=int, default=10)
    commands.add_parser("oracle")
    args = parser.parse_args(argv)
    if args.command == "check":
        return _check()
    if args.command == "run":
        return _run(args.k)
    return _oracle()


if __name__ == "__main__":
    sys.exit(main())
