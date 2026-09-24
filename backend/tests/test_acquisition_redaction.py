"""Secrets in URLs must never reach a result, a log row or an error message. Synthetic keys only."""

import pytest

from app.acquisition.fetch import RawResponse, fetch
from app.acquisition.policy import redact_url, secret_values

SECRET = "SYNTHETIC-SECRET-VALUE"


def resolve(host):
    return ["93.184.216.34"]


class Scripted:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.urls = []

    def __call__(self, url, timeout, max_bytes):
        self.urls.append(url)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(body=b"<html>x</html>"):
    return RawResponse(status=200, headers={}, body=body, truncated=False)


@pytest.mark.parametrize("name", ["api_key", "API_KEY", "apikey", "key", "token", "access_token"])
def test_sensitive_query_parameters_are_redacted(name):
    url = f"https://api.example.org/v2/data?x=1&{name}={SECRET}&y=2"
    assert SECRET not in redact_url(url)
    assert redact_url(url) == f"https://api.example.org/v2/data?x=1&{name}=REDACTED&y=2"


def test_urls_without_secrets_are_unchanged():
    url = "https://example.org/a?frequency=weekly&facets%5Bseries%5D%5B%5D=WCESTUS1"
    assert redact_url(url) == url


def test_secret_values_are_collected_for_scrubbing_text():
    assert secret_values(f"https://x.org/?api_key={SECRET}&a=1") == [SECRET]
    assert secret_values("https://x.org/?a=1") == []


def test_a_fetch_result_never_contains_the_secret_but_the_request_uses_it():
    transport = Scripted(ok())
    url = f"https://api.example.org/v2/data?api_key={SECRET}&length=5"
    result = fetch(url, transport, resolve)
    assert transport.urls == [url]  # the real request carried the key
    assert SECRET not in result.source_url and SECRET not in result.final_url
    assert all(SECRET not in hop for hop in result.redirect_chain)
    assert SECRET not in result.model_dump_json()


def test_a_redirect_that_carries_the_secret_is_redacted_in_the_chain():
    transport = Scripted(
        RawResponse(
            status=302,
            headers={"location": f"https://cdn.example.org/x?api_key={SECRET}"},
            body=b"",
            truncated=False,
        ),
        ok(),
    )
    result = fetch(f"https://api.example.org/a?api_key={SECRET}", transport, resolve)
    assert SECRET not in result.model_dump_json()
    assert result.redirect_chain[-1].endswith("api_key=REDACTED")


def test_an_error_message_that_echoes_the_url_is_scrubbed():
    boom = OSError(f"connection failed for https://api.example.org/a?api_key={SECRET}")
    result = fetch(f"https://api.example.org/a?api_key={SECRET}", Scripted(boom), resolve)
    assert result.outcome == "network_error"
    assert SECRET not in result.error and "REDACTED" in result.error


def test_a_blocked_target_reason_is_scrubbed_too():
    result = fetch(f"http://127.0.0.1/?api_key={SECRET}", Scripted(), resolve)
    assert result.outcome == "blocked_target"
    assert SECRET not in result.model_dump_json()
