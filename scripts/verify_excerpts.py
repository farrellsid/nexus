"""Check that every stored source excerpt really appears in the page it cites.

A source ends in one of four states: `verbatim` (found), `changed` (the page is readable
but the quote is not in it), `unreadable` (the page yields almost no text, for example
because it is script-rendered) or `unreachable` (the fetch failed). Known problems are
declared in `investigations/excerpt-exceptions.json` with a reason; an undeclared problem
fails the run. A second report lists figures in a claim that appear in none of its cited
excerpts, which is how an unsupported claim shows up.

    python scripts/verify_excerpts.py            # both packs
    python scripts/verify_excerpts.py --pack oil
"""

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = {
    "oil": "investigations/02-oil-system/evidence-pack.json",
    "copper": "investigations/01-kamoa-to-cables/evidence-pack.json",
}
EXCEPTIONS = "investigations/excerpt-exceptions.json"
MIN_READABLE = 200  # characters of visible text below which a page counts as unreadable
SKIPPED_TAGS = {"script", "style", "noscript", "template"}
BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "table", "section",
    "article", "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
}  # fmt: skip
REPLACEMENTS = {
    " ": " ", "–": "-", "—": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"',
}  # fmt: skip
DATE_LIKE = re.compile(
    r"\b\d{4}-\d{2}(?:-\d{2})?\b|\b\d{4}-Q\d\b|\b[1-4]Q\d{2}\b|\bQ[1-4]\b|\b(?:19|20)\d{2}\b"
)
FIGURE = re.compile(
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+(?=\s*%)|\d+(?=\s*(?:million|billion|thousand)\b)"
)


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


def normalise(text: str, fold: bool = True) -> str:
    """Make quotes, dashes, spaces and (unless fold is False) case irrelevant."""
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text.casefold() if fold else text


def page_text(markup: str, fold: bool = True) -> str:
    parser = _Text()
    parser.feed(markup)
    return normalise("".join(parser.parts), fold)


def original_span(markup: str, phrase: str) -> str | None:
    """The page's own wording, in its original case, for a phrase; None if absent."""
    raw = page_text(markup, fold=False)
    needle = normalise(phrase)
    start = raw.casefold().find(needle)
    return None if start < 0 else raw[start : start + len(needle)]


def find_excerpt(markup: str, excerpt: str) -> bool:
    """True if the excerpt is a contiguous span of the page's visible text."""
    quote = normalise(excerpt).rstrip(" .,;:!?-…\"'")
    return bool(quote) and quote in page_text(markup)


def classify(markup: str, excerpt: str) -> str:
    if find_excerpt(markup, excerpt):
        return "verbatim"
    return "unreadable" if len(page_text(markup)) < MIN_READABLE else "changed"


def judge(status: str, exception: dict | None) -> str:
    if exception is None:
        return "ok" if status == "verbatim" else "fail"
    if status == exception["status"]:
        return "ok-exception"
    return "stale-exception" if status == "verbatim" else "fail"


def unsupported_figures(statement: str, excerpts: list[str]) -> list[str]:
    """Figures in a claim that appear in none of its cited excerpts."""
    wanted = FIGURE.findall(DATE_LIKE.sub(" ", statement))
    available = {
        token.replace(",", "").rstrip(".")
        for excerpt in excerpts
        for token in re.findall(r"\d[\d,]*(?:\.\d+)?", normalise(excerpt))
    }
    missing = []
    for figure in wanted:
        if figure.replace(",", "") not in available and figure not in missing:
            missing.append(figure)
    return missing


def looks_like_pdf(url: str, content_type: str, head: bytes) -> bool:
    return (
        url.lower().split("?")[0].endswith(".pdf")
        or "pdf" in content_type.lower()
        or head.startswith(b"%PDF")
    )


def fetch(url: str) -> tuple[str, str]:
    """Return (kind, body): kind is ok, pdf or unreachable."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 nexus-verifier"}
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read()
            if looks_like_pdf(url, response.headers.get("Content-Type", ""), raw[:8]):
                return "pdf", ""
            return "ok", raw.decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return "unreachable", type(error).__name__


def verify_source(source: dict) -> str:
    kind, body = fetch(source["url"])
    if kind == "ok":
        return classify(body, source["excerpt"])
    return "unreadable" if kind == "pdf" else "unreachable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pack", choices=(*PACKS, "all"), default="all")
    args = parser.parse_args()
    exceptions_path = ROOT / EXCEPTIONS
    exceptions = (
        json.loads(exceptions_path.read_text("utf-8"))
        if exceptions_path.is_file()
        else {}
    )

    chosen = PACKS if args.pack == "all" else {args.pack: PACKS[args.pack]}
    packs = {
        name: json.loads((ROOT / path).read_text("utf-8"))
        for name, path in chosen.items()
    }
    sources = [s for pack in packs.values() for s in pack["sources"]]
    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(verify_source, sources))

    failures = 0
    for source, status in sorted(
        zip(sources, statuses), key=lambda pair: pair[0]["id"]
    ):
        entry = exceptions.get(source["id"])
        verdict = judge(status, entry)
        failures += verdict == "fail"
        why = f"  ({entry['reason']})" if entry else ""
        print(
            f"{source['id']:6} {status:11} {verdict:16} {source['publisher'][:34]}{why}"
        )

    print(
        "\nClaims with figures absent from every cited excerpt (a review prompt, not proof):"
    )
    flagged = 0
    for pack in packs.values():
        by_id = {s["id"]: s for s in pack["sources"]}
        for claim in pack["claims"]:
            cited = [by_id[i]["excerpt"] for i in claim["evidence_ids"] if i in by_id]
            missing = unsupported_figures(claim["statement"], cited)
            if missing:
                flagged += 1
                print(
                    f"  {claim['id']:6} missing {missing} cited={claim['evidence_ids']}"
                )
    print(
        f"\n{failures} source failure(s); {flagged} claim(s) flagged for figure support"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
