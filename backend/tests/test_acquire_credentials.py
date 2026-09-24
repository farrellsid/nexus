"""Credentials are injected at request time, redacted in the log and never stored. Synthetic key."""

import importlib.util
from pathlib import Path

import pytest

from app.acquisition.fetch import RawResponse
from app.acquisition.snapshots import ObjectStore
from app.storage.acquisition import PostgresAcquisition

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "acquire.py"
SECRET = "SYNTHETIC-EIA-KEY"
API = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/?frequency=weekly&facets%5Bseries%5D%5B%5D=S"
BODY = (
    '{"response":{"data":[{"period":"2026-06-19","series":"S","value":"412134","units":"MBBL"}]},'
    '"request":{"command":"/v2/x"}}'
)


class Recording:
    def __init__(self, body=BODY):
        self.body = body
        self.urls = []

    def __call__(self, url, timeout, max_bytes):
        self.urls.append(url)
        return RawResponse(
            status=200,
            headers={"content-type": "application/json"},
            body=self.body.encode(),
            truncated=False,
        )


def public(host):
    return ["93.184.216.34"]


@pytest.fixture
def acquire(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("acquire_cred", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    key = tmp_path / "eia-key.txt"
    key.write_text(SECRET + "\n", encoding="utf-8")
    monkeypatch.setattr(module, "KEY_FILE", key)
    return module


@pytest.fixture
def env(database, tmp_path):
    return PostgresAcquisition(database), ObjectStore(tmp_path / "objects-root")


def source(acquire, policy="store", url=API):
    return acquire.SourceInfo(id="O-S07", url=url, policy=policy, excerpt="")


def test_the_key_is_added_to_the_request_but_not_to_the_logged_url(acquire, env):
    acquisition, store = env
    transport = Recording()
    acquire.do_fetch(source(acquire), True, acquisition, store, transport, public)
    assert transport.urls[0].endswith(f"&api_key={SECRET}")
    [attempt] = acquisition.attempts("O-S07")
    assert SECRET not in attempt.requested_url and attempt.requested_url.endswith(
        "api_key=REDACTED"
    )
    assert SECRET not in attempt.final_url


def test_other_hosts_never_receive_the_key(acquire, env):
    acquisition, store = env
    transport = Recording()
    acquire.do_fetch(
        source(acquire, url="https://example.org/data.json"),
        True,
        acquisition,
        store,
        transport,
        public,
    )
    assert SECRET not in transport.urls[0]


def test_a_json_response_is_extracted_and_recorded(acquire, env, database):
    acquisition, store = env
    acquire.do_fetch(source(acquire), True, acquisition, store, Recording(), public)
    [attempt] = acquisition.attempts("O-S07")
    assert acquisition.extraction_text_hash(attempt.sha256) is not None


def test_a_body_that_contains_the_secret_is_never_stored(acquire, env):
    acquisition, store = env
    leaky = Recording(BODY.replace("/v2/x", f"/v2/x?api_key={SECRET}"))
    acquire.do_fetch(source(acquire, "store"), True, acquisition, store, leaky, public)
    [attempt] = acquisition.attempts("O-S07")
    assert attempt.outcome == "ok" and attempt.stored is False
    assert store.get(attempt.sha256) is None
