"""Statistics Canada full-table CSV downloads (for example table 25-10-0081-01).

The zip holds the data CSV and a metadata CSV; only the data is read. A missing value keeps
StatCan's symbol as the flag, and the scalar factor stays with the series so a value is never
silently rescaled.
"""

import csv
import io
import zipfile

from app.acquisition.providers.observation import Observation

REQUIRED = ["REF_DATE", "GEO", "Supply and disposition", "Products", "UOM", "VALUE"]


def parse_zip(data: bytes, source_url: str) -> list[Observation]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        member = next(
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv") and "metadata" not in name.lower()
        )
        text = archive.read(member).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"StatCan CSV is missing columns: {', '.join(missing)}")
    observations = []
    for row in reader:
        raw = (row["VALUE"] or "").strip()
        flag = (row.get("SYMBOL") or row.get("STATUS") or "").strip() or None
        observations.append(
            Observation(
                provider="statcan",
                series={
                    "geo": row["GEO"],
                    "products": row["Products"],
                    "disposition": row["Supply and disposition"],
                    "scalar": (row.get("SCALAR_FACTOR") or "").strip(),
                },
                period=row["REF_DATE"],
                value_text=raw or None,
                unit=row["UOM"],
                flag=flag,
                source_url=source_url,
            )
        )
    return observations


def select(
    observations: list[Observation], geo: str, products: str, disposition: str
) -> list[Observation]:
    return [
        o
        for o in observations
        if o.series["geo"] == geo
        and o.series["products"] == products
        and o.series["disposition"] == disposition
    ]
