"""The licence gate decides what may ship. These tests pin its behaviour with synthetic data."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_licences.py"
ALLOWED = {"MIT", "Apache-2.0", "ISC", "BSD-3-Clause"}


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("check_licences", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def codes(findings, level=None):
    return sorted(f.code for f in findings if level is None or f.level == level)


def rights(**overrides):
    entry = {
        "publisher": "Agency",
        "redistribution": "allowed",
        "release_excerpt": "include",
        "snapshot_policy": "hash_only",
        "basis": "Published as public domain",
        "evidence_url": "https://example.org/terms",
        "checked_at": "2026-09-23",
    }
    return entry | overrides


SOURCES = [{"id": "S1", "publisher": "Agency"}]


class TestSources:
    def test_a_source_without_a_rights_entry_is_an_error_in_every_mode(self, gate):
        for mode in ("dev", "release"):
            findings = gate.evaluate_sources(SOURCES, {}, mode)
            assert codes(findings, "error") == ["source-missing-rights"]

    def test_a_source_without_a_snapshot_policy_is_an_error(self, gate):
        entry = {k: v for k, v in rights().items() if k != "snapshot_policy"}
        assert codes(gate.evaluate_sources(SOURCES, {"S1": entry}, "dev"), "error") == [
            "source-bad-snapshot-policy"
        ]

    def test_an_unknown_snapshot_policy_is_an_error(self, gate):
        entry = rights(snapshot_policy="keep_everything")
        assert codes(gate.evaluate_sources(SOURCES, {"S1": entry}, "dev"), "error") == [
            "source-bad-snapshot-policy"
        ]

    def test_each_valid_snapshot_policy_passes(self, gate):
        for policy in ("store", "hash_only", "none"):
            entry = rights(snapshot_policy=policy)
            assert gate.evaluate_sources(SOURCES, {"S1": entry}, "dev") == []

    def test_a_rights_entry_for_no_source_is_an_error(self, gate):
        findings = gate.evaluate_sources(SOURCES, {"S1": rights(), "S9": rights()}, "dev")
        assert codes(findings, "error") == ["rights-entry-orphan"]

    def test_an_allowed_source_passes(self, gate):
        assert gate.evaluate_sources(SOURCES, {"S1": rights()}, "release") == []

    def test_an_unverified_source_included_blocks_release_but_not_development(self, gate):
        entry = rights(redistribution="unverified", release_excerpt="include")
        assert codes(gate.evaluate_sources(SOURCES, {"S1": entry}, "release"), "error") == [
            "source-unverified-included"
        ]
        assert codes(gate.evaluate_sources(SOURCES, {"S1": entry}, "dev"), "error") == []

    def test_an_unverified_source_with_its_excerpt_withheld_can_be_released(self, gate):
        entry = rights(redistribution="unverified", release_excerpt="withhold")
        findings = gate.evaluate_sources(SOURCES, {"S1": entry}, "release")
        assert codes(findings, "error") == []
        assert codes(findings, "note") == ["source-withheld"]

    def test_a_blocked_source_can_never_be_included(self, gate):
        entry = rights(redistribution="blocked", release_excerpt="include")
        for mode in ("dev", "release"):
            findings = gate.evaluate_sources(SOURCES, {"S1": entry}, mode)
            assert codes(findings, "error") == ["source-blocked-included"]


COMPONENTS = [
    {
        "id": "app",
        "redistribution": "allowed",
        "included": True,
        "emitted_globs": ["index.html", "assets/*"],
    },
    {"id": "cesium", "redistribution": "allowed", "included": True, "emitted_globs": ["cesium/**"]},
    {
        "id": "fonts",
        "redistribution": "unverified",
        "included": True,
        "emitted_globs": ["fonts/**"],
    },
    {
        "id": "models",
        "redistribution": "blocked",
        "included": False,
        "forbidden_globs": ["models/*.glb"],
    },
]


class TestEmittedFiles:
    def test_files_covered_by_allowed_components_pass(self, gate):
        files = ["index.html", "assets/app.js", "cesium/Workers/a.js", "cesium/Assets/deep/b.png"]
        assert gate.evaluate_dist(files, COMPONENTS, "release") == []

    def test_a_file_that_no_component_covers_is_an_error(self, gate):
        findings = gate.evaluate_dist(["index.html", "mystery/logo.svg"], COMPONENTS, "dev")
        assert codes(findings, "error") == ["emitted-uncovered"]

    def test_star_does_not_cross_directories_but_double_star_does(self, gate):
        findings = gate.evaluate_dist(["assets/nested/x.js"], COMPONENTS, "dev")
        assert codes(findings, "error") == ["emitted-uncovered"]

    def test_a_file_from_an_unverified_component_blocks_release_only(self, gate):
        assert codes(gate.evaluate_dist(["fonts/a.woff2"], COMPONENTS, "release"), "error") == [
            "emitted-unverified"
        ]
        assert codes(gate.evaluate_dist(["fonts/a.woff2"], COMPONENTS, "dev"), "error") == []

    def test_a_forbidden_file_is_an_error_in_every_mode(self, gate):
        for mode in ("dev", "release"):
            findings = gate.evaluate_dist(["index.html", "models/jet.glb"], COMPONENTS, mode)
            assert "emitted-forbidden" in codes(findings, "error")


class TestLicenceExpressions:
    @pytest.mark.parametrize(
        ("expression", "verdict"),
        [
            ("MIT", "allowed"),
            ("(MIT OR GPL-3.0)", "allowed"),
            ("Apache-2.0 AND MIT", "allowed"),
            ("Apache-2.0 AND GPL-3.0", "review"),
            ("GPL-3.0", "review"),
            ("SEE LICENSE IN LICENSE", "review"),
            ("", "review"),
            (None, "review"),
        ],
    )
    def test_expression_verdicts(self, gate, expression, verdict):
        assert gate.judge_licence(expression, ALLOWED) == verdict


class TestNpmRuntime:
    """The reader is asked for a package by its lockfile path, so nested copies are found."""

    LOCK = {
        "packages": {
            "": {},
            "node_modules/fine": {},
            "node_modules/build-only": {"dev": True},
            "node_modules/@scope/copyleft": {},
            "node_modules/undeclared": {},
            "node_modules/host/node_modules/@scope/nested": {},
        }
    }
    LICENCES = {
        "node_modules/fine": "MIT",
        "node_modules/build-only": "GPL-3.0",
        "node_modules/@scope/copyleft": "GPL-3.0",
        "node_modules/undeclared": None,
        "node_modules/host/node_modules/@scope/nested": "Apache-2.0",
    }

    def test_only_runtime_packages_with_unapproved_licences_are_flagged(self, gate):
        findings = gate.evaluate_npm_runtime(self.LOCK, self.LICENCES.get, ALLOWED, "release")
        flagged = sorted(f.message.split()[0] for f in findings if f.level == "error")
        assert flagged == ["@scope/copyleft", "undeclared"]

    def test_a_nested_copy_is_judged_by_its_own_licence(self, gate):
        findings = gate.evaluate_npm_runtime(self.LOCK, self.LICENCES.get, ALLOWED, "release")
        assert not any("nested" in f.message for f in findings)

    def test_in_development_the_same_packages_are_notes(self, gate):
        findings = gate.evaluate_npm_runtime(self.LOCK, self.LICENCES.get, ALLOWED, "dev")
        assert codes(findings, "error") == []
        assert len(codes(findings, "note")) == 2


class TestLicenceFiles:
    def test_missing_licence_files_block_release_only(self, gate, tmp_path):
        assert codes(gate.evaluate_licence_files(tmp_path, "release"), "error") == [
            "licence-file-missing",
            "licence-file-missing",
        ]
        assert codes(gate.evaluate_licence_files(tmp_path, "dev"), "error") == []

    def test_present_licence_files_pass(self, gate, tmp_path):
        (tmp_path / "LICENSE").write_text("MIT License", encoding="utf-8")
        (tmp_path / "LICENSE-CONTENT.md").write_text("CC BY 4.0", encoding="utf-8")
        assert gate.evaluate_licence_files(tmp_path, "release") == []
