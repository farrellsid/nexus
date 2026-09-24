"""Reports, comparison keys and reviewed judgements about them.

Disagreement is a relationship between reports, not a replacement value. The machine only
proposes candidate groups; a person decides whether reports are comparable.
"""

from datetime import date
from typing import Literal

from app.knowledge import Record

REQUIRED_SCOPE = ("geography", "population", "methodology", "seasonal_adjustment")


class Period(Record):
    kind: Literal["interval", "instant", "unknown"]
    start: date | None
    end_exclusive: date | None
    at: date | None


class Report(Record):
    id: str
    entity: str | None
    measure: str
    statistic: str
    unit_symbol: str
    period: Period
    value_text: str
    epistemic_status: str
    release_status: str
    source_ids: list[str]
    origin_groups: list[str]
    scope: dict[str, str | None] = {}  # metadata the packs do not yet hold


class Membership(Record):
    report_id: str
    assessment: Literal["comparable", "not_comparable", "unresolved"]
    reason: str
    reviewer: str


class Relation(Record):
    left: str
    right: str
    relation: Literal["contradicts", "revises", "duplicates_origin", "different_scope", "supports"]
    rationale: str
    reviewer: str


def is_forecast(report: Report) -> bool:
    return report.epistemic_status == "forecast"


def metadata_gaps(report: Report) -> list[str]:
    """Scope metadata still missing; missing means unresolved, never equal."""
    return sorted(name for name in REQUIRED_SCOPE if not report.scope.get(name))


def comparison_key(report: Report) -> tuple | None:
    """Entity, measure, statistic, unit and complete period; None when any is missing."""
    period = report.period
    complete = (period.kind == "interval" and period.start and period.end_exclusive) or (
        period.kind == "instant" and period.at
    )
    if not (report.entity and report.measure and report.statistic and report.unit_symbol):
        return None
    if not complete:
        return None
    return (
        report.entity,
        report.measure,
        report.statistic,
        report.unit_symbol,
        period.kind,
        str(period.start),
        str(period.end_exclusive),
        str(period.at),
    )


def candidate_groups(reports: list[Report]) -> list[list[Report]]:
    """Reports with the same key and lane from at least two distinct origin groups."""
    buckets: dict[tuple, list[Report]] = {}
    for report in reports:
        key = comparison_key(report)
        if key is not None:
            buckets.setdefault((key, is_forecast(report)), []).append(report)
    groups = []
    for _, members in sorted(buckets.items(), key=lambda item: str(item[0])):
        origins = {origin for report in members for origin in report.origin_groups}
        if len(members) >= 2 and len(origins) >= 2:
            groups.append(sorted(members, key=lambda report: report.id))
    return groups
