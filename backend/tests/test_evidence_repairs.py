"""Evidence repairs never edit history: they plan corrections that a person then reviews."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "propose_evidence_repairs.py"
PACKS = {
    "oil": ROOT / "investigations" / "02-oil-system" / "evidence-pack.json",
    "copper": ROOT / "investigations" / "01-kamoa-to-cables" / "evidence-pack.json",
}
REPAIRS = ROOT / "investigations" / "02-oil-system" / "repairs"


@pytest.fixture(scope="module")
def repairs():
    spec = importlib.util.spec_from_file_location("propose_evidence_repairs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLAIMS = {"C1": ["S1", "S2"], "C2": ["S1"]}
KNOWN = {"S1", "S2", "S3", "S4"}


class TestPlanning:
    def test_replace_swaps_a_source_in_place_and_keeps_order(self, repairs):
        plan = repairs.plan_corrections(
            CLAIMS, [{"claim_id": "C1", "replace": {"S1": "S3"}, "why": "w"}], KNOWN
        )
        assert [(p.claim_id, p.before, p.after) for p in plan] == [
            ("C1", ["S1", "S2"], ["S3", "S2"])
        ]

    def test_add_appends_a_source_the_claim_does_not_yet_cite(self, repairs):
        plan = repairs.plan_corrections(
            CLAIMS, [{"claim_id": "C2", "add": ["S4"], "why": "w"}], KNOWN
        )
        assert plan[0].after == ["S1", "S4"]

    def test_replacing_a_source_the_claim_does_not_cite_is_an_error(self, repairs):
        with pytest.raises(ValueError, match="does not cite"):
            repairs.plan_corrections(
                CLAIMS, [{"claim_id": "C2", "replace": {"S2": "S3"}, "why": "w"}], KNOWN
            )

    def test_an_unknown_new_source_is_an_error(self, repairs):
        with pytest.raises(ValueError, match="unknown source"):
            repairs.plan_corrections(CLAIMS, [{"claim_id": "C1", "add": ["S9"], "why": "w"}], KNOWN)

    def test_a_correction_that_changes_nothing_is_an_error(self, repairs):
        with pytest.raises(ValueError, match="changes nothing"):
            repairs.plan_corrections(CLAIMS, [{"claim_id": "C1", "add": ["S1"], "why": "w"}], KNOWN)

    def test_an_unknown_claim_is_an_error(self, repairs):
        with pytest.raises(ValueError, match="unknown claim"):
            repairs.plan_corrections(CLAIMS, [{"claim_id": "C9", "add": ["S4"], "why": "w"}], KNOWN)

    def test_two_corrections_for_one_claim_are_an_error(self, repairs):
        twice = [
            {"claim_id": "C1", "add": ["S3"], "why": "a"},
            {"claim_id": "C1", "add": ["S4"], "why": "b"},
        ]
        with pytest.raises(ValueError, match="more than once"):
            repairs.plan_corrections(CLAIMS, twice, KNOWN)

    def test_a_correction_without_a_reason_is_an_error(self, repairs):
        with pytest.raises(ValueError, match="reason"):
            repairs.plan_corrections(CLAIMS, [{"claim_id": "C1", "add": ["S3"]}], KNOWN)


def load(name):
    return json.loads(PACKS[name].read_text(encoding="utf-8"))


class TestPackConsistency:
    def test_the_coverage_label_is_not_earlier_than_the_latest_evidence(self):
        pack = load("oil")
        dates = [s["published_on"] for s in pack["sources"] if s["published_on"]]
        dates += [e["published_on"] for e in pack["events"] if e.get("published_on")]
        label = pack["briefing"]["developments_through"]
        assert label >= max(dates), f"label {label} is earlier than evidence dated {max(dates)}"

    def test_the_scope_text_states_the_same_date_as_the_label(self):
        pack = load("oil")
        assert pack["briefing"]["developments_through"] in pack["scope"]

    @pytest.mark.skipif(not REPAIRS.is_dir(), reason="no repair mappings yet")
    def test_every_repair_mapping_plans_cleanly_against_the_real_pack(self, repairs):
        pack = load("oil")
        claims = {c["id"]: c["evidence_ids"] for c in pack["claims"]}
        known = {s["id"] for s in pack["sources"]}
        for path in sorted(REPAIRS.glob("*.json")):
            mapping = json.loads(path.read_text(encoding="utf-8"))
            assert repairs.plan_corrections(claims, mapping["corrections"], known)
