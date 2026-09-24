"""EIA Open Data API v2: build a keyed request and parse a page of results.

The key appears only in the URL that is sent. Everything stored or logged goes through
`redact_url`. Values keep their original text; nothing is rounded or converted here.
"""

import json
from urllib.parse import urlencode

from app.acquisition.providers.observation import Observation
from app.knowledge import Record

BASE = "https://api.eia.gov/v2"
NOT_SERIES = {"period", "value", "units", "unit"}


class EiaQuery(Record):
    route: str  # for example petroleum/stoc/wstk
    frequency: str | None = None
    facets: dict[str, list[str]] = {}
    start: str | None = None
    end: str | None = None


class EiaPage(Record):
    total: int
    warnings: list[str]
    observations: list[Observation]


def build_url(query: EiaQuery, key: str, offset: int = 0, length: int = 5000) -> str:
    """The request URL. The key is last so a redacting logger never has to guess."""
    params: list[tuple[str, str]] = []
    if query.frequency:
        params.append(("frequency", query.frequency))
    params.append(("data[0]", "value"))
    for name, values in sorted(query.facets.items()):
        params += [(f"facets[{name}][]", value) for value in values]
    if query.start:
        params.append(("start", query.start))
    if query.end:
        params.append(("end", query.end))
    params += [
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("offset", str(offset)),
        ("length", str(length)),
    ]
    return f"{BASE}/{query.route}/data/?{urlencode(params)}&api_key={key}"


def parse_page(body: bytes, source_url: str) -> EiaPage:
    """Parse one response page. An error body raises rather than returning an empty result."""
    document = json.loads(body)
    if "error" in document:
        error = document["error"]
        detail = (
            f"{error.get('code', '')} {error.get('message', '')}"
            if isinstance(error, dict)
            else str(error)
        )
        raise ValueError(f"EIA returned an error: {detail.strip()}")
    response = document["response"]
    rows = response.get("data", [])
    observations = [
        Observation(
            provider="eia",
            series={k: str(v) for k, v in row.items() if k not in NOT_SERIES and v is not None},
            period=str(row["period"]),
            value_text=None if row.get("value") is None else str(row["value"]),
            unit=str(row.get("units") or row.get("unit") or ""),
            flag=None,
            source_url=source_url,
        )
        for row in rows
    ]
    warnings = [
        f"{w.get('warning', '')}: {w.get('description', '')}".strip(": ")
        for w in document.get("warnings", [])
    ]
    return EiaPage(
        total=int(response.get("total", len(rows))), warnings=warnings, observations=observations
    )
