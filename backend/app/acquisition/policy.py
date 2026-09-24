"""What Nexus may fetch and what it may keep. Both rules default to the cautious answer."""

import ipaddress
import re
from collections.abc import Callable
from typing import Literal
from urllib.parse import urlsplit

# store: keep the bytes locally. hash_only: keep the hash, size, headers and outcome, discard the
# bytes. none: keep nothing but the attempt itself. Unverified rights default to hash_only.
SnapshotPolicy = Literal["store", "hash_only", "none"]


# Query parameters whose values are credentials. They are sent on the wire but never logged.
_SECRET_PARAMETER = re.compile(
    r"([?&](?:api_key|apikey|key|token|access_token|auth|password|secret)=)([^&#]*)", re.I
)
REDACTED = "REDACTED"


def redact_url(url: str) -> str:
    """The URL with credential query values replaced, safe to log or store."""
    return _SECRET_PARAMETER.sub(lambda m: m.group(1) + REDACTED, url)


def secret_values(url: str) -> list[str]:
    """The credential values in a URL, so text that echoes the URL can be scrubbed."""
    return [m.group(2) for m in _SECRET_PARAMETER.finditer(url) if m.group(2)]


def scrub(text: str | None, secrets: list[str]) -> str | None:
    """Remove every known secret from free text, such as an error message."""
    if text is None:
        return None
    for secret in secrets:
        text = text.replace(secret, REDACTED)
    return redact_url(text)


def guard_storage(policy: SnapshotPolicy) -> bool:
    """True only when the source's policy permits keeping the fetched bytes."""
    return policy == "store"


def _blocked(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def check_target(url: str, resolve: Callable[[str], list[str]]) -> str | None:
    """None if the URL may be fetched, otherwise the reason it may not."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return f"scheme {parts.scheme!r} is not allowed"
    if parts.username or parts.password:
        return "credentials in the URL are not allowed"
    host = parts.hostname
    if not host:
        return "the URL has no host"
    try:
        addresses = [str(ipaddress.ip_address(host))]
    except ValueError:
        addresses = resolve(host)
    if not addresses:
        return f"host {host} does not resolve"
    for address in addresses:
        if _blocked(address):
            return f"address {address} is private, loopback, link-local or reserved"
    return None
