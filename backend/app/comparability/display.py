"""Side-by-side display data for reports, built only from reviewed judgements.

Cards are always shown. A range appears only when at least two independent reports have been
assessed comparable by a reviewer; it is never a confidence interval and never averaged.
"""

from decimal import Decimal

from app.comparability.model import Membership, Relation, Report, is_forecast, metadata_gaps
from app.knowledge import Record


class Card(Record):
    report_id: str
    label: str
    value_text: str
    unit_symbol: str
    period_label: str
    source_ids: list[str]
    lane: str  # "reported" or "forecast"; lanes never share a range
    revised_from: list[str]
    difference: str | None


class Range(Record):
    low: str
    high: str
    n: int
    label: str


class ComparisonDisplay(Record):
    cards: list[Card]
    range: Range | None
    notes: list[str]


def _period_label(report: Report) -> str:
    period = report.period
    if period.kind == "interval":
        return f"{period.start} to <{period.end_exclusive}"
    if period.kind == "instant":
        return f"at {period.at}"
    return "period unknown"


def _independent_groups(reports: list[Report], relations: list[Relation]) -> int:
    """Count origin components: a shared origin group or a declared duplicate joins reports."""
    parent = {report.id: report.id for report in reports}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def join(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    seen: dict[str, str] = {}
    for report in reports:
        for origin in report.origin_groups:
            if origin in seen:
                join(report.id, seen[origin])
            seen[origin] = report.id
    for relation in relations:
        if (
            relation.relation == "duplicates_origin"
            and {relation.left, relation.right} <= parent.keys()
        ):
            join(relation.left, relation.right)
    return len({find(report.id) for report in reports})


def build_display(
    reports: list[Report], memberships: list[Membership], relations: list[Relation]
) -> ComparisonDisplay:
    superseded = {r.right for r in relations if r.relation == "revises"}
    revised_from: dict[str, list[str]] = {}
    for relation in relations:
        if relation.relation == "revises":
            revised_from.setdefault(relation.left, []).append(relation.right)
    active = [report for report in reports if report.id not in superseded]
    assessment = {membership.report_id: membership for membership in memberships}
    scope_notes: dict[str, str] = {}
    for relation in relations:
        if relation.relation == "different_scope":
            scope_notes[relation.left] = scope_notes[relation.right] = relation.rationale
    several = len(active) > 1

    def difference(report: Report) -> str | None:
        if not several:
            return None
        judged = assessment.get(report.id)
        if judged is None:
            return scope_notes.get(report.id) or "comparability not yet reviewed"
        if judged.assessment == "not_comparable":
            return judged.reason
        if judged.assessment == "unresolved":
            return f"unresolved: {judged.reason}"
        return scope_notes.get(report.id)

    cards = [
        Card(
            report_id=report.id,
            label=report.measure.replace("_", " "),
            value_text=report.value_text,
            unit_symbol=report.unit_symbol,
            period_label=_period_label(report),
            source_ids=report.source_ids,
            lane="forecast" if is_forecast(report) else "reported",
            revised_from=revised_from.get(report.id, []),
            difference=difference(report),
        )
        for report in active
    ]
    notes: list[str] = []
    if not several:
        return ComparisonDisplay(cards=cards, range=None, notes=notes)

    comparable = [
        report
        for report in active
        if (judged := assessment.get(report.id)) and judged.assessment == "comparable"
    ]
    if len(comparable) < 2:
        notes.append("no range: fewer than two reports are assessed comparable by a reviewer")
        return ComparisonDisplay(cards=cards, range=None, notes=notes)
    if len({is_forecast(report) for report in comparable}) > 1:
        notes.append("no range: forecast and reported values are never combined")
    if len({report.unit_symbol for report in comparable}) > 1:
        notes.append("no range: the units differ")
    gaps = {report.id: metadata_gaps(report) for report in comparable if metadata_gaps(report)}
    if gaps:
        detail = "; ".join(f"{rid}: {', '.join(missing)}" for rid, missing in sorted(gaps.items()))
        notes.append(f"no range: scope metadata is missing ({detail})")
    independent = _independent_groups(comparable, relations)
    if independent < 2:
        notes.append("no range: the comparable reports share one origin")
    if notes:
        return ComparisonDisplay(cards=cards, range=None, notes=notes)

    ordered = sorted(comparable, key=lambda report: Decimal(report.value_text))
    return ComparisonDisplay(
        cards=cards,
        range=Range(
            low=ordered[0].value_text,
            high=ordered[-1].value_text,
            n=independent,
            label=f"range of {independent} reports; not a confidence interval",
        ),
        notes=notes,
    )
