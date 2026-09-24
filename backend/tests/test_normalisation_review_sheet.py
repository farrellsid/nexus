"""The review sheet is what the user reads to approve the mapping; it must show everything."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "render_normalisation_review.py"
RELEASE = ROOT / "normalisation" / "releases" / "2026-09-24.json"


@pytest.fixture(scope="module")
def renderer():
    spec = importlib.util.spec_from_file_location("render_normalisation_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sheet(renderer):
    return renderer.render(RELEASE)


def test_every_claim_and_entity_appears(sheet):
    import json

    release = json.loads(RELEASE.read_text("utf-8"))
    for claim in release["claims"]:
        assert f"| {claim['claim_id']} |" in sheet
    for entity in release["entities"]:
        assert f"`{entity['canonical_id']}`" in sheet


def test_the_decisions_for_the_reader_come_first(sheet):
    assert sheet.index("Decisions for you") < sheet.index("## Claims")


def test_rendering_is_deterministic(renderer):
    assert renderer.render(RELEASE) == renderer.render(RELEASE)


def test_flagged_claims_are_marked(sheet):
    for line in sheet.splitlines():
        if line.startswith("| O-C12 |"):
            assert "REVIEW" in line
