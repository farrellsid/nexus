"""GDELT DOC API: a discovery layer that lists news articles, never a source of figures.

Articles are leads for the acquire pipeline. Each carries a machine-coded provenance label so no
GDELT record is mistaken for a reviewed claim. GDELT asks for citation of the GDELT Project with a
link to https://www.gdeltproject.org/ wherever its data is used or redistributed.
"""

import json
from datetime import datetime
from urllib.parse import urlencode

from app.knowledge import Record

BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RECORDS = 250  # a hard cap of our own; one request never asks for more
MIN_SECONDS_BETWEEN_REQUESTS = (
    6  # GDELT states no limit; we stay well under one request per five seconds
)


class Article(Record):
    url: str
    title: str
    seen_at: str  # ISO 8601 UTC
    domain: str
    language: str
    source_country: str
    provenance: str = "gdelt-machine-coded"


def build_query_url(query: str, timespan: str = "7d", maxrecords: int = 25) -> str:
    if not 1 <= maxrecords <= MAX_RECORDS:
        raise ValueError(f"maxrecords must be between 1 and {MAX_RECORDS}")
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": str(maxrecords),
        "timespan": timespan,
        "format": "json",
        "sort": "datedesc",
    }
    return f"{BASE}?{urlencode(params)}"


def _iso(seen: str) -> str:
    try:
        return datetime.strptime(seen, "%Y%m%dT%H%M%SZ").strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return seen


def parse_articles(body: str) -> list[Article]:
    """Articles from a DOC API reply; an empty, non-JSON or message-only reply is no articles."""
    try:
        document = json.loads(body)
    except ValueError:
        return []
    return [
        Article(
            url=item.get("url", ""),
            title=item.get("title", ""),
            seen_at=_iso(item.get("seendate", "")),
            domain=item.get("domain", ""),
            language=item.get("language", ""),
            source_country=item.get("sourcecountry", ""),
        )
        for item in document.get("articles", [])
        if item.get("url")
    ]
