"""Cross-check the oil pack's metric values against EIA and JODI structured data.

    python scripts/crosscheck.py             # dry run: prints the requests it would make
    python scripts/crosscheck.py --confirm   # makes the requests once and writes the report

Run from `backend/` with PYTHONPATH=. like the other scripts. The EIA key is read from
`.local/eia-api-key.txt`, sent only in the request, and redacted everywhere it could be logged.
Response bytes are kept under `.local/objects/` (the user's `store` decision); a body that contains
a known secret is never stored. Nothing here writes to the database, loops or schedules.
"""

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "normalisation" / "releases" / "2026-09-24.json"
VOCABULARY = ROOT / "normalisation" / "vocabulary-v1.json"
KEY_FILE = ROOT / ".local" / "eia-api-key.txt"
REPORT = ROOT / "docs" / "crosscheck-report.md"
MANIFEST = ROOT / ".local" / "crosscheck-manifest.json"
JODI_URL = "https://www.jodidata.org/_resources/files/downloads/oil-data/annual-csv/primary/primaryyear2026.csv"
JODI_AREAS = {
    "place/saudi-arabia": "SA",
    "place/iraq": "IQ",
    "place/russia": "RU",
    "place/iran": "IR",
}
EIA_AREAS = {
    "place/saudi-arabia": "SAU",
    "place/iraq": "IRQ",
    "place/russia": "RUS",
    "place/iran": "IRN",
}
OIL = "oil-system-2025q3-2026q2"


def eia_queries():
    from app.acquisition.providers.eia import EiaQuery

    return {
        "stocks": EiaQuery(
            route="petroleum/stoc/wstk",
            frequency="weekly",
            facets={"series": ["WCESTUS1"]},
            start="2026-06-01",
            end="2026-09-30",
        ),
        "utilization": EiaQuery(
            route="petroleum/pnp/wiup",
            frequency="weekly",
            facets={"series": ["WPULEUS3"]},
            start="2026-06-01",
            end="2026-09-30",
        ),
        "capacity": EiaQuery(
            route="petroleum/pnp/cap1",
            frequency="annual",
            facets={"series": ["8_NA_8D0_NUS_4"]},
            start="2025",
            end="2026",
        ),
        "country production": EiaQuery(
            route="international",
            frequency="monthly",
            facets={
                "productId": ["57"],
                "activityId": ["1"],
                "countryRegionId": sorted(EIA_AREAS.values()),
                "unit": ["TBPD"],
            },
            start="2026-01",
            end="2026-09",
        ),
    }


def _load_measurements():
    from app.normalisation.release import Release
    from app.normalisation.vocabulary import load_vocabulary

    release = Release.model_validate_json(RELEASE.read_text("utf-8"))
    return {m.id: m for m in release.measurements}, load_vocabulary(VOCABULARY)


def _fetch(url, label, store, manifest, secrets):
    from app.acquisition.fetch import Limits, fetch

    result = fetch(url, limits=Limits(max_bytes=20_000_000, timeout_seconds=90))
    kept = None
    if result.outcome == "ok" and not any(s.encode() in result.body for s in secrets):
        stored = store.put(result.body, "store")
        kept = str(stored.path.relative_to(ROOT)) if stored else None
    manifest.append(
        {
            "label": label,
            "url": result.source_url,
            "final_url": result.final_url,
            "outcome": result.outcome,
            "error": result.error,
            "status": result.status,
            "bytes": result.byte_count,
            "sha256": result.sha256,
            "stored_at": kept,
            "retrieved_at": result.ended_at.isoformat(),
        }
    )
    return result


def run(confirm: bool) -> int:
    from app.acquisition.policy import redact_url
    from app.acquisition.providers.crosscheck import cross_check
    from app.acquisition.providers.eia import build_url, parse_page
    from app.acquisition.providers.jodi import parse_csv
    from app.acquisition.snapshots import ObjectStore

    measurements, vocabulary = _load_measurements()
    key = KEY_FILE.read_text("utf-8").strip()
    queries = eia_queries()
    print("requests (keys redacted):")
    for name, query in queries.items():
        print(f"  EIA {name}: {redact_url(build_url(query, key))}")
    print(f"  JODI: {JODI_URL}")
    if not confirm:
        print("\ndry run: nothing fetched; add --confirm to make these requests once")
        return 0

    store, manifest = ObjectStore(ROOT / ".local"), []
    eia = {}
    for name, query in queries.items():
        result = _fetch(build_url(query, key), f"EIA {name}", store, manifest, [key])
        if result.outcome == "ok":
            page = parse_page(result.body, result.source_url)
            for warning in page.warnings:
                print(f"  warning ({name}): {warning}")
            eia[name] = page.observations
        else:
            eia[name] = []
            print(f"  EIA {name}: {result.outcome} {result.error}")
    jodi_result = _fetch(JODI_URL, "JODI primary 2026", store, manifest, [key])
    jodi = (
        parse_csv(jodi_result.body.decode("utf-8", "replace"), jodi_result.source_url)
        if jodi_result.outcome == "ok"
        else []
    )

    def unit_of(measurement):
        return vocabulary.measures[measurement.measure].unit

    rows = []
    for index in (0, 1, 2):
        m = measurements[f"{OIL}:O-M07:{index}"]
        rows.append(
            cross_check(
                m.id,
                m.original_label,
                m.value_text,
                unit_of(m),
                eia["stocks"],
                {"series": "WCESTUS1"},
                str(m.temporal.valid_at),
                "MBBL",
            )
        )
    for index in (0, 1):
        m = measurements[f"{OIL}:O-M09:{index}"]
        week_ending = m.temporal.valid_end_exclusive - timedelta(days=1)
        rows.append(
            cross_check(
                m.id,
                m.original_label,
                m.value_text,
                unit_of(m),
                eia["utilization"],
                {"series": "WPULEUS3"},
                str(week_ending),
                "%",
            )
        )
    for index in (0, 1):
        m = measurements[f"{OIL}:O-M08:{index}"]
        rows.append(
            cross_check(
                m.id,
                m.original_label,
                m.value_text,
                unit_of(m),
                eia["capacity"],
                {"series": "8_NA_8D0_NUS_4"},
                str(m.temporal.valid_at.year),
                "B/CD",
            )
        )
    for index in range(4):
        m = measurements[f"{OIL}:O-M11:{index}"]
        period = m.temporal.valid_start.strftime("%Y-%m")
        area = JODI_AREAS[m.entity]
        rows.append(
            cross_check(
                m.id + " vs JODI",
                m.original_label,
                m.value_text,
                unit_of(m),
                jodi,
                {"area": area, "product": "CRUDEOIL", "flow": "INDPROD"},
                period,
                "KBD",
            )
        )
        rows.append(
            cross_check(
                m.id + " vs EIA international",
                m.original_label,
                m.value_text,
                unit_of(m),
                eia["country production"],
                {"countryRegionId": EIA_AREAS[m.entity]},
                period,
                "TBPD",
            )
        )

    counts = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    print()
    for row in rows:
        print(
            f"{row.status:24} {row.measurement_id.split(':', 1)[1]:28} pack {row.pack_value:>7}  provider {row.provider_value or '-':>12}  {row.note[:80]}"
        )
    print("\ncounts:", counts)
    _write_report(rows, counts, manifest)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"report: {REPORT.relative_to(ROOT)}; manifest (hashes, redacted URLs): {MANIFEST.relative_to(ROOT)}"
    )
    return 0


def _write_report(rows, counts, manifest):
    lines = [
        "# Provider cross-check report",
        "",
        f"Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC by `scripts/crosscheck.py`. Raw counts: "
        + ", ".join(f"{n} {status}" for status, n in sorted(counts.items()))
        + ".",
        "",
        "A cross-check is not a verdict on the pack. `equal_at_pack_precision` means the provider's own number, scaled exactly and rounded half-up to the pack's decimal places, equals the pack's value. It does not show the pack cited that provider. `differs` may be a different definition, month or vintage, and needs a person. `no_observation` means the provider does not (yet) publish that period.",
        "",
        "| Measurement | Label | Pack | Provider (scaled) | Provider raw | Status | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.measurement_id.split(':', 1)[1]} | {row.label} | {row.pack_value} | {row.provider_value or '-'} | {row.provider_raw or '-'} | {row.status} | {row.note} |"
        )
    lines += [
        "",
        "## Requests (keys redacted)",
        "",
        "| Request | Outcome | Bytes | SHA-256 |",
        "|---|---|---|---|",
    ]
    for item in manifest:
        lines.append(
            f"| {item['label']} | {item['outcome']} | {item['bytes']} | `{(item['sha256'] or '-')[:16]}` |"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--confirm", action="store_true")
    return run(parser.parse_args(argv).confirm)


if __name__ == "__main__":
    sys.exit(main())
