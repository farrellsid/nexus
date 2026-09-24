"""Original decimal text of metric values, kept free of any float round trip."""

import json
from pathlib import Path


def read_metric_points(pack_path: Path) -> dict[str, list[str]]:
    """Map each metric ID to the original text of its point values, in point order."""
    pack = json.loads(pack_path.read_text("utf-8"), parse_float=str, parse_int=str)
    metrics = (pack.get("briefing") or {}).get("metrics", [])
    return {metric["id"]: [point["value"] for point in metric["points"]] for metric in metrics}
