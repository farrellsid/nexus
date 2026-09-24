"""Collect data from the other providers, one polite request each. Dry run by default.

    python scripts/collect.py statcan [--confirm]
    python scripts/collect.py sodir   [--confirm]
    python scripts/collect.py gdelt --query '"Strait of Hormuz" sourcelang:eng' [--confirm]
    python scripts/collect.py probe   [--confirm]     # one request each to sources that may block scripts

Run from `backend/` with PYTHONPATH=. like the other scripts. Requests identify themselves
honestly. A site that refuses (HTTP 403, 412, a certificate failure) is recorded as refused and
left for a manual download: nothing here spoofs a browser, retries around a block, or disables
certificate checks. Response bytes are kept under `.local/objects/` (the user's `store` decision).
GDELT data must be cited as the GDELT Project, https://www.gdeltproject.org/.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".local" / "collect-manifest.json"
STATCAN_URL = "https://www150.statcan.gc.ca/n1/tbl/csv/25100081-eng.zip"
SODIR_BASE = (
    "https://factpages.sodir.no/public?/Factpages/external/tableview/{}"
    "&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used&CultureCode=en"
    "&rs:Format=CSV"
)
# The plain field export is capped at 300 rows by Sodir; the national total has every month.
SODIR_TABLES = {
    "NCS total, monthly": "field_production_totalt_NCS_month__DisplayAllRows",
    "by field, monthly (capped)": "field_production_monthly",
}
PROBES = {
    "OPEC monthly report page": "https://www.opec.org/monthly-oil-market-report.html",
    "Energy Institute data page": "https://energyinst.org/statistical-review/resources-and-data-downloads",
    "GEM oil infrastructure page": "https://globalenergymonitor.org/projects/global-oil-infrastructure-tracker",
    "China NBS (English)": "https://www.stats.gov.cn/english/",
    "China customs preliminary release": "http://english.customs.gov.cn/statics/report/preliminary.html",
    "China customs coverage of major imports": "http://english.customs.gov.cn/Statistics/Statistics?ColumnId=6",
    "Brazil ANP production by well": "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/producao-de-petroleo-e-gas-natural-por-poco",
}


def _fetch(url, label, manifest):
    from app.acquisition.fetch import Limits, fetch
    from app.acquisition.snapshots import ObjectStore

    result = fetch(url, limits=Limits(max_bytes=30_000_000, timeout_seconds=90))
    stored = (
        ObjectStore(ROOT / ".local").put(result.body, "store")
        if result.outcome == "ok"
        else None
    )
    manifest.append(
        {
            "label": label,
            "url": result.source_url,
            "outcome": result.outcome,
            "error": result.error,
            "status": result.status,
            "content_type": result.content_type,
            "bytes": result.byte_count,
            "sha256": result.sha256,
            "stored_at": str(stored.path.relative_to(ROOT)) if stored else None,
            "retrieved_at": result.ended_at.isoformat(),
        }
    )
    _save(manifest[-1:])
    return result


def _save(manifest):
    history = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else []
    MANIFEST.write_text(json.dumps(history + manifest, indent=2), encoding="utf-8")


def run_statcan(confirm):
    from app.acquisition.providers.statcan import parse_zip

    print(f"StatCan table 25-10-0081-01: {STATCAN_URL}")
    if not confirm:
        return print("dry run: nothing fetched")
    manifest = []
    result = _fetch(STATCAN_URL, "StatCan 25100081", manifest)
    if result.outcome != "ok":
        return print(f"refused or failed: {result.outcome} {result.error}")
    observations = parse_zip(result.body, result.source_url)
    periods = sorted({o.period for o in observations})
    crude = sorted(
        {
            o.series["products"]
            for o in observations
            if "crude" in o.series["products"].lower()
        }
    )
    print(
        f"{len(observations)} observations, {periods[0]} to {periods[-1]}; crude-like products: {crude or 'none'}"
    )


def run_sodir(confirm):
    from app.acquisition.providers.sodir import parse_csv

    for label, table in SODIR_TABLES.items():
        url = SODIR_BASE.format(table)
        print(f"Sodir production {label}: {url[:96]}...")
        if not confirm:
            continue
        manifest = []
        result = _fetch(url, f"Sodir {label}", manifest)
        if result.outcome != "ok":
            print(f"  refused or failed: {result.outcome} {result.error}")
            continue
        observations = parse_csv(
            result.body.decode("utf-8", "replace"), result.source_url
        )
        periods = sorted({o.period for o in observations})
        fields = sorted({o.series["field"] for o in observations})
        print(
            f"  {len(observations)} observations ({len(observations) // 6} rows), {len(fields)} field(s), {periods[0]} to {periods[-1]}"
        )
        if len(observations) // 6 == 300:
            print(
                "  note: exactly 300 rows; the export is capped, not the full history"
            )
    if not confirm:
        print("dry run: nothing fetched")


def run_gdelt(query, timespan, maxrecords, confirm):
    from app.acquisition.providers.gdelt import build_query_url, parse_articles

    url = build_query_url(query, timespan, maxrecords)
    print(f"GDELT DOC API (one request, discovery only): {url}")
    if not confirm:
        return print("dry run: nothing fetched")
    manifest = []
    result = _fetch(url, f"GDELT {query[:40]}", manifest)
    if result.outcome != "ok":
        return print(f"refused or failed: {result.outcome} {result.error}")
    articles = parse_articles(result.body.decode("utf-8", "replace"))
    print(
        f"{len(articles)} candidate article(s); each is a lead, machine-coded by GDELT, not evidence"
    )
    for article in articles[:15]:
        print(f"  {article.seen_at} {article.domain:28} {article.title[:80]}")
    print("Data: the GDELT Project, https://www.gdeltproject.org/")


def run_probe(confirm):
    print("one plain request each (refusals are recorded, never worked around):")
    for label, url in PROBES.items():
        print(f"  {label}: {url}")
    if not confirm:
        return print("dry run: nothing fetched")
    manifest = []
    for label, url in PROBES.items():
        result = _fetch(url, label, manifest)
        detail = f"{result.outcome} status={result.status} bytes={result.byte_count}"
        print(
            f"{label:42} {detail} {('| ' + result.error[:70]) if result.error else ''}"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("statcan", "sodir", "probe"):
        commands.add_parser(name).add_argument("--confirm", action="store_true")
    gdelt = commands.add_parser("gdelt")
    gdelt.add_argument("--query", required=True)
    gdelt.add_argument("--timespan", default="7d")
    gdelt.add_argument("--maxrecords", type=int, default=25)
    gdelt.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    print(f"{datetime.now(UTC):%Y-%m-%d %H:%M} UTC")
    if args.command == "statcan":
        run_statcan(args.confirm)
    elif args.command == "sodir":
        run_sodir(args.confirm)
    elif args.command == "gdelt":
        run_gdelt(args.query, args.timespan, args.maxrecords, args.confirm)
    else:
        run_probe(args.confirm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
