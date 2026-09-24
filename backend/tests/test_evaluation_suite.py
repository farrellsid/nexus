"""The real eval suite covers every authored question and stays deterministic."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "evaluate.py"
SUITE = ROOT / "evals" / "industry-v1" / "suite.json"

pytestmark = pytest.mark.skipif(not SUITE.exists(), reason="suite not authored yet")


@pytest.fixture(scope="module")
def evaluate():
    spec = importlib.util.spec_from_file_location("evaluate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def loaded(evaluate):
    return evaluate._load()


def test_the_suite_validates_against_the_real_packs(evaluate, loaded):
    suite, release, investigations, acceptance, _ = loaded
    assert evaluate.validate(suite, release, investigations, acceptance) == []


def test_the_suite_covers_all_26_authored_questions(loaded):
    suite, _, _, acceptance, _ = loaded
    assert len(acceptance) == 26
    assert sorted(case.id for case in suite.cases) == sorted(acceptance)
    copper = [c for c in suite.cases if not c.id.startswith("O-")]
    assert (len(copper), len(suite.cases) - len(copper)) == (12, 14)


def test_confirmed_oracles_are_counted_in_the_diff(loaded):
    """Confirmation is the user's act: this count changes only when they confirm cases."""
    suite = loaded[0]
    assert sum(c.oracle_review_status == "user_confirmed" for c in suite.cases) == 0


def test_the_run_is_deterministic(evaluate, capsys):
    evaluate.main(["run", "--k", "10"])
    first = capsys.readouterr().out
    evaluate.main(["run", "--k", "10"])
    assert capsys.readouterr().out == first


def test_the_check_command_passes(evaluate, capsys):
    assert evaluate.main(["check"]) == 0
    assert "26 cases" in capsys.readouterr().out
