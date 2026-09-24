"""Deterministic text extraction from HTML, and exact passage location.

The same bytes always give the same text and hash. Unlike the excerpt verifier, extraction keeps
the page's own case, quotes and dashes, so a passage located here is a true quotation, not a folded
match.
"""

import hashlib
import json
import re
from html.parser import HTMLParser

from app.knowledge import Record

EXTRACTOR = "nexus-html-text/1"
JSON_EXTRACTOR = "nexus-json-data/1"
# Fields that describe a row rather than identify or measure it are left out of the canonical text.
DESCRIPTIVE = re.compile(r"(-name|-description|Name|Description)$")
MIN_READABLE = 200  # characters of visible text below which a page is a shell, not content
SKIPPED_TAGS = {"script", "style", "noscript", "template"}
BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "table", "section", "article",
    "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "thead", "tbody",
}  # fmt: skip


class TextExtraction(Record):
    text: str
    text_sha256: str
    extractor: str
    readable: bool


class Passage(Record):
    start: int
    end: int
    text: str


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIPPED_TAGS:
            self._skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in SKIPPED_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_text(markup: str) -> TextExtraction:
    parser = _Text()
    parser.feed(markup)
    text = collapse("".join(parser.parts))
    return TextExtraction(
        text=text,
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        extractor=EXTRACTOR,
        readable=len(text) >= MIN_READABLE,
    )


def extract_json_rows(body: str) -> TextExtraction:
    """Canonical text for an API response: its data rows only, sorted keys, no whitespace.

    Response metadata (request echo, API version) is excluded, so a version bump does not look like
    a change in the data. An error body, empty data or invalid JSON is not readable.
    """
    try:
        rows = json.loads(body).get("response", {}).get("data", [])
    except (ValueError, AttributeError):
        rows = []
    if not isinstance(rows, list):
        rows = []
    text = (
        "["
        + ",".join(
            json.dumps(
                {
                    k: v
                    for k, v in sorted(row.items())
                    if v is not None and not DESCRIPTIVE.search(k)
                },
                separators=(",", ":"),
                ensure_ascii=False,
            )
            for row in rows
        )
        + "]"
    )
    return TextExtraction(
        text=text,
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        extractor=JSON_EXTRACTOR,
        readable=bool(rows),
    )


def find_passage(text: str, phrase: str) -> Passage | None:
    """The exact span of `phrase` in `text`; only whitespace is folded, never case or characters."""
    needle = collapse(phrase)
    if not needle:
        return None
    start = text.find(needle)
    if start < 0:
        return None
    return Passage(start=start, end=start + len(needle), text=text[start : start + len(needle)])
