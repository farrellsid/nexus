"""Norwegian Offshore Directorate (Sodir) monthly saleable production by field.

Oil, gas, NGL, condensate and oil equivalent are separate measures in different units
(million or billion standard cubic metres) and are never merged.
"""

import csv
import io

from app.acquisition.providers.observation import Observation

MEASURES = {
    "prfPrdOilNetMillSm3": ("oil", "MillSm3"),
    "prfPrdGasNetBillSm3": ("gas", "BillSm3"),
    "prfPrdNGLNetMillSm3": ("ngl", "MillSm3"),
    "prfPrdCondensateNetMillSm3": ("condensate", "MillSm3"),
    "prfPrdOeNetMillSm3": ("oil_equivalent", "MillSm3"),
    "prfPrdProducedWaterInFieldMillSm3": ("produced_water", "MillSm3"),
}
REQUIRED = ["prfYear", "prfMonth", *MEASURES]  # the national total has no field column


def parse_csv(text: str, source_url: str) -> list[Observation]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"Sodir CSV is missing columns: {', '.join(missing)}")
    observations = []
    for row in reader:
        period = f"{row['prfYear']}-{int(row['prfMonth']):02d}"
        for column, (measure, unit) in MEASURES.items():
            raw = (row[column] or "").strip()
            observations.append(
                Observation(
                    provider="sodir",
                    series={
                        "field": row.get("prfInformationCarrier") or "NCS total",
                        "measure": measure,
                    },
                    period=period,
                    value_text=raw or None,
                    unit=unit,
                    flag=None,
                    source_url=source_url,
                )
            )
    return observations
