"""JODI oil CSV downloads: parse rows into observations.

`-` and `x` are JODI symbols standing where a number would be. They are kept as flags and never
turned into zero. What each symbol means has not been verified against JODI's manual.
"""

import csv
import io

from app.acquisition.providers.observation import Observation

REQUIRED = [
    "REF_AREA",
    "TIME_PERIOD",
    "ENERGY_PRODUCT",
    "FLOW_BREAKDOWN",
    "UNIT_MEASURE",
    "OBS_VALUE",
]
NOT_A_NUMBER = {"", "-", "x"}


def parse_csv(text: str, source_url: str) -> list[Observation]:
    reader = csv.DictReader(io.StringIO(text))
    missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"JODI CSV is missing columns: {', '.join(missing)}")
    observations = []
    for row in reader:
        raw = (row["OBS_VALUE"] or "").strip()
        observations.append(
            Observation(
                provider="jodi",
                series={
                    "area": row["REF_AREA"],
                    "product": row["ENERGY_PRODUCT"],
                    "flow": row["FLOW_BREAKDOWN"],
                    "assessment": (row.get("ASSESSMENT_CODE") or "").strip(),
                },
                period=row["TIME_PERIOD"],
                value_text=None if raw in NOT_A_NUMBER else raw,
                unit=row["UNIT_MEASURE"],
                flag=raw if raw in NOT_A_NUMBER and raw else None,
                source_url=source_url,
            )
        )
    return observations


def select(
    observations: list[Observation],
    areas: list[str],
    product: str,
    flow: str,
    unit: str,
) -> list[Observation]:
    return [
        o
        for o in observations
        if o.series["area"] in areas
        and o.series["product"] == product
        and o.series["flow"] == flow
        and o.unit == unit
    ]
