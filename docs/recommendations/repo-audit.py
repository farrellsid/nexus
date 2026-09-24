"""Read-only evidence inventory for the technical design review; JSON to stdout.

Run from the Nexus root with: .venv/Scripts/python -B docs/recommendations/repo-audit.py
No imports from app.main, network requests, database writes, or generated code.
"""

import collections
import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parents[2]
reference = root / ".local/references/gods-eye-view"
packs = []
claims = []
sources = []
for path in sorted((root / "investigations").glob("*/evidence-pack.json")):
    data = json.loads(path.read_text("utf-8"))
    questions = json.loads((path.parent / "acceptance-cases.json").read_text("utf-8"))
    metrics = data.get("briefing", {}).get("metrics", [])
    claims.extend(data["claims"])
    sources.extend(data["sources"])
    packs.append({
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "case_id": data["case_id"],
        "counts": {key: len(data[key]) for key in ("entities", "claims", "sources", "events")},
        "questions": len(questions),
        "question_statuses": dict(collections.Counter(q["status"] for q in questions)),
        "metric_groups": len(metrics),
        "metric_points": sum(len(m["points"]) for m in metrics),
        "metric_summary": [{"id": m["id"], "unit": m["unit"], "period_labels": [p["period"] for p in m["points"]]} for m in metrics],
    })

asset_paths = set()
for folder in (reference / "public", reference / "src/data/local_data", reference / "src/ui/styles", reference / "src/layers/alpr/assets", reference / "docs/media"):
    if folder.exists():
        asset_paths.update(p for p in folder.rglob("*") if p.is_file())
asset_paths.update(p for p in (reference / "style.css", reference / "index.html", reference / "LICENSE", reference / "DATA_SOURCES.md", reference / "src/data/bhoteKoshiFloodPath.js") if p.exists())
assets = [{"path": p.relative_to(reference).as_posix(), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(asset_paths)]
third_party_path = reference / "node_modules/cesium/ThirdParty.json"
control_root = root / ".local/postgres-runtime/pgsql/share/extension"
report = {
    "scope": "Read-only filesystem/JSON inspection; not source truth, licence clearance or executed acceptance evaluation",
    "packs": packs,
    "predicates": dict(sorted(collections.Counter(c["predicate"] for c in claims).items())),
    "kinds": dict(sorted(collections.Counter(c["kind"] for c in claims).items())),
    "source_statuses": dict(sorted(collections.Counter(s["review_status"] for s in sources).items())),
    "claims_with_unknown_validity": [c["id"] for c in claims if c["valid_from"] is None and c["valid_to"] is None],
    "all_candidates": all(c["review_status"] == "manually_source_checked_candidate" for c in claims),
    "all_ground_truth_false": all(c["ground_truth"] is False for c in claims),
    "claim_inventory": [{key: c[key] for key in ("id", "predicate", "kind", "subject", "object", "source_as_of", "valid_from", "valid_to", "recorded_on")} for c in claims],
    "extension_controls_present": [name for name in ("pg_trgm", "unaccent", "fuzzystrmatch", "vector", "postgis") if (control_root / (name + ".control")).exists()],
    "root_licence_files": [p.name for p in root.iterdir() if p.is_file() and p.name.lower().startswith(("license", "licence"))],
    "reference_asset_inventory": assets,
    "cesium_third_party_declarations_not_independent_clearance": json.loads(third_party_path.read_text("utf-8")) if third_party_path.exists() else None,
}
print(json.dumps(report, ensure_ascii=True, indent=2))
