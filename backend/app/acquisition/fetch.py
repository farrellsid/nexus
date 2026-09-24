"""Fetch one public page with hard limits. The transport is injectable so tests never use a network.

Every hop of every redirect is checked against the target policy, and every attempt ends in a
named outcome. Only bytes actually received are hashed; nothing is invented when a fetch fails.
"""

import hashlib
import http.client
import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urljoin, urlsplit

from app.acquisition.policy import check_target, redact_url, scrub, secret_values
from app.knowledge import Record

USER_AGENT = "nexus-acquire/0.1"
TOOL = USER_AGENT
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
Outcome = Literal[
    "ok",
    "access_denied",
    "network_error",
    "http_error",
    "blocked_target",
    "too_large",
    "too_many_redirects",
]


@dataclass(frozen=True)
class Limits:
    max_bytes: int = 5_000_000
    max_redirects: int = 5
    timeout_seconds: float = 25.0


class RawResponse(Record):
    status: int
    headers: dict[str, str]  # lower-case names
    body: bytes
    truncated: bool


Transport = Callable[[str, float, int], RawResponse]  # (url, timeout, max_bytes); never redirects


class FetchResult(Record):
    source_url: str
    final_url: str
    redirect_chain: list[str]
    status: int | None
    content_type: str | None
    etag: str | None
    last_modified: str | None
    byte_count: int
    sha256: str | None
    body: bytes
    outcome: Outcome
    error: str | None
    started_at: datetime
    ended_at: datetime


def default_resolver(host: str) -> list[str]:
    try:
        return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})
    except OSError:
        return []


def default_transport(url: str, timeout: float, max_bytes: int) -> RawResponse:
    """A plain GET: no cookies, no auth, no compression, no redirects, a capped body."""
    parts = urlsplit(url)
    connection_class = (
        http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
    )
    connection = connection_class(parts.hostname, parts.port, timeout=timeout)
    try:
        target = parts.path or "/"
        if parts.query:
            target += "?" + parts.query
        connection.request(
            "GET", target, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        )
        response = connection.getresponse()
        body = response.read(max_bytes + 1)
        return RawResponse(
            status=response.status,
            headers={name.lower(): value for name, value in response.getheaders()},
            body=body[:max_bytes] if len(body) > max_bytes else body,
            truncated=len(body) > max_bytes,
        )
    finally:
        connection.close()


def fetch(
    url: str,
    transport: Transport = default_transport,
    resolve: Callable[[str], list[str]] = default_resolver,
    limits: Limits = Limits(),
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FetchResult:
    started = clock()
    chain = [url]
    current = url

    def result(
        outcome: Outcome, error: str | None = None, raw: RawResponse | None = None, body=b""
    ):
        headers = raw.headers if raw else {}
        secrets = [s for hop in chain for s in secret_values(hop)]
        return FetchResult(
            source_url=redact_url(url),
            final_url=redact_url(current),
            redirect_chain=[redact_url(hop) for hop in chain],
            status=raw.status if raw else None,
            content_type=headers.get("content-type"),
            etag=headers.get("etag"),
            last_modified=headers.get("last-modified"),
            byte_count=len(body),
            sha256=hashlib.sha256(body).hexdigest() if outcome == "ok" else None,
            body=body if outcome == "ok" else b"",
            outcome=outcome,
            error=scrub(error, secrets),
            started_at=started,
            ended_at=clock(),
        )

    for hop in range(limits.max_redirects + 1):
        reason = check_target(current, resolve)
        if reason:
            return result("blocked_target", reason)
        try:
            raw = transport(current, limits.timeout_seconds, limits.max_bytes)
        except Exception as error:  # a transport may fail in many ways; all are network errors
            return result("network_error", f"{type(error).__name__}: {error}")
        location = raw.headers.get("location")
        if raw.status in REDIRECT_STATUSES and location:
            if hop == limits.max_redirects:
                return result(
                    "too_many_redirects", f"more than {limits.max_redirects} redirects", raw
                )
            current = urljoin(current, location)
            chain.append(current)
            continue
        if raw.status in (401, 403, 451):
            return result("access_denied", f"status {raw.status}", raw)
        if raw.status == 429 or raw.status >= 500:
            return result("network_error", f"status {raw.status}", raw)
        if raw.status >= 400:
            return result("http_error", f"status {raw.status}", raw)
        if raw.truncated or len(raw.body) > limits.max_bytes:
            return result("too_large", f"body exceeds {limits.max_bytes} bytes", raw)
        return result("ok", None, raw, raw.body)
    return result("too_many_redirects", "redirect loop")  # unreachable; keeps the type total
