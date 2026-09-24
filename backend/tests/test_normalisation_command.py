"""The normalise command's check must fail loudly on an incomplete release."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "normalise.py"
RELEASE = ROOT / "normalisation" / "releases" / "2026-09-24.json"


@pytest.fixture(scope="module")
def normalise():
    spec = importlib.util.spec_from_file_location("normalise", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_authored_release_passes_the_check(normalise, capsys):
    assert normalise.check(RELEASE) == []


def test_dropping_a_claim_fails_the_check_with_a_readable_message(normalise, tmp_path, capsys):
    data = json.loads(RELEASE.read_text("utf-8"))
    data["claims"] = [c for c in data["claims"] if c["claim_id"] != "O-C26"]
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(data), encoding="utf-8")
    problems = normalise.check(broken)
    assert any("missing claim" in p and "O-C26" in p for p in problems)


def test_main_check_exits_nonzero_on_problems(normalise, tmp_path, capsys):
    data = json.loads(RELEASE.read_text("utf-8"))
    data["sources"] = data["sources"][:-1]
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(data), encoding="utf-8")
    assert normalise.main(["check", "--release", str(broken)]) == 1
    assert "missing source" in capsys.readouterr().out


def test_main_check_exits_zero_on_the_authored_release(normalise, capsys):
    assert normalise.main(["check", "--release", str(RELEASE)]) == 0
    assert "0 problem" in capsys.readouterr().out
