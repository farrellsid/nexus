"""Safe fetching: target rules, redirects, limits and outcomes. No test touches the network."""

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.acquisition.fetch import Limits, RawResponse, default_transport, fetch
from app.acquisition.policy import check_target, guard_storage

PUBLIC = {"example.org": ["93.184.216.34"], "cdn.example.org": ["93.184.216.35"]}


def resolve(host):
    return PUBLIC.get(host, ["10.1.2.3"] if host == "internal.example.org" else [])


class Scripted:
    """A fake transport that returns queued responses and records the URLs it was asked for."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.urls = []

    def __call__(self, url, timeout, max_bytes):
        self.urls.append(url)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(body=b"<html>hello</html>", **headers):
    return RawResponse(
        status=200, headers={"content-type": "text/html", **headers}, body=body, truncated=False
    )


def redirect(location, status=302):
    return RawResponse(status=status, headers={"location": location}, body=b"", truncated=False)


class TestTargets:
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://[::1]/",
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://169.254.169.254/latest/meta-data",
            "http://0.0.0.0/",
            "http://[::ffff:10.0.0.1]/",
            "http://internal.example.org/",
            "file:///etc/passwd",
            "ftp://example.org/x",
            "https://user:pw@example.org/",
        ],
    )
    def test_unsafe_targets_are_rejected(self, url):
        assert check_target(url, resolve) is not None

    def test_a_public_target_is_allowed(self):
        assert check_target("https://example.org/report", resolve) is None

    def test_a_host_that_does_not_resolve_is_rejected(self):
        assert "resolve" in check_target("https://nowhere.example/", resolve)

    def test_only_a_store_policy_permits_keeping_bytes(self):
        assert [guard_storage(p) for p in ("store", "hash_only", "none")] == [True, False, False]


class TestFetch:
    def test_a_public_page_is_fetched_and_hashed_over_the_exact_bytes(self):
        body = b"<html>exact bytes</html>"
        result = fetch("https://example.org/a", Scripted(ok(body, etag='"abc"')), resolve)
        assert result.outcome == "ok"
        assert result.sha256 == hashlib.sha256(body).hexdigest()
        assert (result.byte_count, result.etag, result.content_type) == (
            len(body),
            '"abc"',
            "text/html",
        )
        assert result.final_url == "https://example.org/a" and result.error is None
        assert result.started_at <= result.ended_at

    def test_an_unsafe_target_is_blocked_before_any_request(self):
        transport = Scripted()
        result = fetch("http://127.0.0.1/", transport, resolve)
        assert result.outcome == "blocked_target" and transport.urls == []
        assert result.sha256 is None

    def test_a_redirect_is_followed_and_recorded(self):
        transport = Scripted(redirect("https://cdn.example.org/b"), ok())
        result = fetch("https://example.org/a", transport, resolve)
        assert result.outcome == "ok"
        assert result.redirect_chain == ["https://example.org/a", "https://cdn.example.org/b"]
        assert result.final_url == "https://cdn.example.org/b"

    def test_a_relative_redirect_resolves_against_the_current_url(self):
        transport = Scripted(redirect("/moved/here"), ok())
        fetch("https://example.org/a/b", transport, resolve)
        assert transport.urls == ["https://example.org/a/b", "https://example.org/moved/here"]

    def test_a_redirect_to_a_private_address_is_blocked_at_that_hop(self):
        transport = Scripted(redirect("http://169.254.169.254/latest"))
        result = fetch("https://example.org/a", transport, resolve)
        assert result.outcome == "blocked_target"
        assert result.redirect_chain[-1] == "http://169.254.169.254/latest"
        assert len(transport.urls) == 1

    def test_too_many_redirects_are_refused(self):
        transport = Scripted(*[redirect("/next")] * 7)
        result = fetch("https://example.org/a", transport, resolve, Limits(max_redirects=5))
        assert result.outcome == "too_many_redirects"

    @pytest.mark.parametrize("status", [401, 403, 451])
    def test_refusals_are_access_denied(self, status):
        response = RawResponse(status=status, headers={}, body=b"no", truncated=False)
        assert (
            fetch("https://example.org/a", Scripted(response), resolve).outcome == "access_denied"
        )

    @pytest.mark.parametrize("status", [429, 500, 503])
    def test_server_trouble_is_a_network_error(self, status):
        response = RawResponse(status=status, headers={}, body=b"", truncated=False)
        result = fetch("https://example.org/a", Scripted(response), resolve)
        assert result.outcome == "network_error" and str(status) in result.error

    def test_other_client_errors_are_http_errors(self):
        response = RawResponse(status=404, headers={}, body=b"", truncated=False)
        assert fetch("https://example.org/a", Scripted(response), resolve).outcome == "http_error"

    def test_a_transport_failure_is_a_network_error(self):
        result = fetch("https://example.org/a", Scripted(TimeoutError("slow")), resolve)
        assert result.outcome == "network_error" and "TimeoutError" in result.error

    def test_an_oversize_body_is_refused_and_not_hashed(self):
        big = RawResponse(status=200, headers={}, body=b"x" * 11, truncated=False)
        result = fetch("https://example.org/a", Scripted(big), resolve, Limits(max_bytes=10))
        assert result.outcome == "too_large" and result.sha256 is None and result.body == b""

    def test_a_truncated_body_is_refused(self):
        cut = RawResponse(status=200, headers={}, body=b"x", truncated=True)
        assert fetch("https://example.org/a", Scripted(cut), resolve).outcome == "too_large"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"a" * 100 if self.path == "/big" else b"<html>local</html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def local_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_the_default_transport_reads_a_local_server_and_caps_the_body(local_server):
    small = default_transport(f"{local_server}/small", 5, 1000)
    assert (small.status, small.body, small.truncated) == (200, b"<html>local</html>", False)
    assert small.headers["content-type"] == "text/html"
    big = default_transport(f"{local_server}/big", 5, 10)
    assert big.truncated and len(big.body) <= 11
