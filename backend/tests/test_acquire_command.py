"""The acquire command is the only network path; tests drive it with a fake transport."""

import importlib.util
from pathlib import Path

import pytest

from app.acquisition.fetch import RawResponse
from app.acquisition.snapshots import ObjectStore
from app.storage.acquisition import PostgresAcquisition

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "acquire.py"
PAGE = (
    "<html><body><p>"
    + "Stable synthetic paragraph for the fixture page. " * 8
    + "</p><p>Exports increased to 13.6 million barrels per day (b/d) in April</p></body></html>"
)


class Scripted:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, url, timeout, max_bytes):
        self.calls += 1
        return self.responses.pop(0)


def page(body=PAGE):
    return RawResponse(
        status=200, headers={"content-type": "text/html"}, body=body.encode(), truncated=False
    )


def public(host):
    return ["93.184.216.34"]


@pytest.fixture(scope="module")
def acquire():
    spec = importlib.util.spec_from_file_location("acquire", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def env(database, tmp_path):
    return PostgresAcquisition(database), ObjectStore(tmp_path)


def source(
    acquire,
    policy="hash_only",
    excerpt="Exports increased to 13.6 million barrels per day (b/d) in April",
):
    return acquire.SourceInfo(
        id="O-S07", url="https://example.org/exports", policy=policy, excerpt=excerpt
    )


def test_a_dry_run_fetches_nothing_and_writes_nothing(acquire, env, capsys):
    acquisition, store = env
    transport = Scripted()
    acquire.do_fetch(source(acquire), False, acquisition, store, transport, public)
    assert transport.calls == 0 and acquisition.attempts("O-S07") == []
    assert "dry run" in capsys.readouterr().out


def test_a_hash_only_fetch_logs_the_attempt_and_stores_no_bytes(acquire, env, tmp_path):
    acquisition, store = env
    acquire.do_fetch(source(acquire), True, acquisition, store, Scripted(page()), public)
    [attempt] = acquisition.attempts("O-S07")
    assert attempt.outcome == "ok" and attempt.stored is False and attempt.sha256
    assert list(tmp_path.rglob("*")) == []


def test_a_store_policy_source_keeps_exactly_one_object(acquire, env):
    acquisition, store = env
    acquire.do_fetch(source(acquire, "store"), True, acquisition, store, Scripted(page()), public)
    [attempt] = acquisition.attempts("O-S07")
    assert attempt.stored is True and store.get(attempt.sha256) == PAGE.encode()


def test_a_blocked_target_is_logged_and_nothing_is_stored(acquire, env, tmp_path):
    acquisition, store = env
    bad = acquire.SourceInfo(id="O-S07", url="http://127.0.0.1/x", policy="store", excerpt="x")
    transport = Scripted()
    acquire.do_fetch(bad, True, acquisition, store, transport, public)
    [attempt] = acquisition.attempts("O-S07")
    assert attempt.outcome == "blocked_target" and transport.calls == 0
    assert list(tmp_path.rglob("*")) == []


def test_verify_without_a_baseline_says_baseline_missing(acquire, env):
    acquisition, store = env
    acquire.do_verify(source(acquire), True, acquisition, store, Scripted(page()), public)
    [row] = acquisition.verifications("O-S07")
    assert (row.state, row.reason, row.comparison_readiness) == (
        "unreachable",
        "baseline_missing",
        "not_ready",
    )


def test_baseline_then_verify_matches_and_finds_the_stored_excerpt(acquire, env):
    acquisition, store = env
    acquire.do_fetch(source(acquire), True, acquisition, store, Scripted(page()), public)
    [attempt] = acquisition.attempts("O-S07")
    acquire.do_baseline("O-S07", attempt.id, "Synthetic reviewer", "first snapshot", acquisition)
    acquire.do_verify(source(acquire), True, acquisition, store, Scripted(page()), public)
    [row] = acquisition.verifications("O-S07")
    assert (row.state, row.comparison_readiness) == ("matches", "ready")
    assert row.passages[0]["found"] is True


def test_a_changed_page_verifies_as_changed(acquire, env):
    acquisition, store = env
    acquire.do_fetch(source(acquire), True, acquisition, store, Scripted(page()), public)
    [attempt] = acquisition.attempts("O-S07")
    acquire.do_baseline("O-S07", attempt.id, "Synthetic reviewer", "first snapshot", acquisition)
    changed = PAGE.replace("13.6", "12.9")
    acquire.do_verify(source(acquire), True, acquisition, store, Scripted(page(changed)), public)
    [row] = acquisition.verifications("O-S07")
    assert row.state == "changed" and row.passages[0]["found"] is False


def test_an_unreachable_page_verifies_as_unreachable_not_offline(acquire, env):
    acquisition, store = env
    acquire.do_fetch(source(acquire), True, acquisition, store, Scripted(page()), public)
    [attempt] = acquisition.attempts("O-S07")
    acquire.do_baseline("O-S07", attempt.id, "Synthetic reviewer", "first snapshot", acquisition)
    gone = RawResponse(status=503, headers={}, body=b"", truncated=False)
    acquire.do_verify(source(acquire), True, acquisition, store, Scripted(gone), public)
    [row] = acquisition.verifications("O-S07")
    assert (row.state, row.reason) == ("unreachable", "network_error")


def test_a_verify_dry_run_does_not_fetch(acquire, env):
    acquisition, store = env
    transport = Scripted()
    acquire.do_verify(source(acquire), False, acquisition, store, transport, public)
    assert transport.calls == 0 and acquisition.verifications("O-S07") == []


def test_source_info_reads_the_pack_and_the_rights_policy(acquire):
    import json

    info = acquire.load_source("O-S07")
    rights = json.loads(acquire.RIGHTS.read_text("utf-8"))["sources"]["O-S07"]
    assert info.url.startswith("https://www.eia.gov/")
    assert info.policy == rights["snapshot_policy"]
    with pytest.raises(SystemExit):
        acquire.load_source("NOPE")


def test_a_source_without_a_rights_entry_defaults_to_hash_only(acquire, tmp_path, monkeypatch):
    empty = tmp_path / "rights.json"
    empty.write_text('{"sources": {}}', encoding="utf-8")
    monkeypatch.setattr(acquire, "RIGHTS", empty)
    assert acquire.load_source("O-S07").policy == "hash_only"
