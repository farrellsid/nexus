"""Read-only research graph. Candidate assertions never become accepted facts on import."""

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from app.evidence import Source, validate_references


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Entity(Record):
    id: str
    name: str
    type: str
    coordinates: tuple[float, float] | None
    location_note: str
    location_precision: str | None = None


class Claim(Record):
    id: str
    subject: str
    predicate: str
    object: str
    evidence_ids: list[str]
    kind: str
    # Research sources include fiscal-year labels, not only exact publication dates.
    source_as_of: str | None
    valid_from: date | None
    valid_to: date | None
    recorded_on: date
    statement: str
    caveat: str
    review_status: str
    ground_truth: bool


class Event(Record):
    id: str
    event_time: str | None
    precision: str
    published_on: date | None = None
    source_ids: list[str]
    kind: str
    description: str


class MetricPoint(Record):
    period: str
    value: float
    status: str


class MetricSeries(Record):
    id: str
    title: str
    unit: str
    description: str
    source_ids: list[str]
    points: list[MetricPoint]
    caveat: str


class Briefing(Record):
    title: str
    window_start: date
    window_end: date
    developments_through: date
    framing: str
    metrics: list[MetricSeries]


class EvidencePack(Record):
    schema_version: str
    case_id: str
    checked_on: date
    scope: str
    verdict: str
    sources: list[Source]
    entities: list[Entity]
    claims: list[Claim]
    events: list[Event]
    excluded_assertions: list[str] = []
    briefing: Briefing | None = None

    @model_validator(mode="after")
    def validate_graph(self) -> "EvidencePack":
        for records in (self.sources, self.entities, self.claims, self.events):
            ids = [record.id for record in records]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate record IDs")
        entity_ids = {entity.id for entity in self.entities}
        for claim in self.claims:
            if not {claim.subject, claim.object} <= entity_ids:
                raise ValueError(f"Unresolved endpoints for {claim.id}")
            validate_references(claim.evidence_ids, self.sources)
            if claim.valid_from and claim.valid_to and claim.valid_from > claim.valid_to:
                raise ValueError(f"Reversed valid-time interval for {claim.id}")
        for event in self.events:
            validate_references(event.source_ids, self.sources)
        if self.briefing:
            connected = {
                endpoint for claim in self.claims for endpoint in (claim.subject, claim.object)
            }
            isolated = entity_ids - connected
            if isolated:
                raise ValueError(
                    f"Briefing contains isolated entities: {', '.join(sorted(isolated))}"
                )
            metric_ids = [metric.id for metric in self.briefing.metrics]
            if len(metric_ids) != len(set(metric_ids)):
                raise ValueError("Duplicate metric IDs")
            for metric in self.briefing.metrics:
                validate_references(metric.source_ids, self.sources)
                if not metric.points:
                    raise ValueError(f"Metric {metric.id} has no points")
        return self


class Neighborhood(Record):
    entities: list[Entity]
    claims: list[Claim]
    sources: list[Source]


def neighborhood(pack: EvidencePack, entity_id: str, depth: int = 1) -> Neighborhood:
    """Explore incident links in either direction; retain each assertion's direction.

    Reachability is navigational, never evidence of a physical material flow.
    """
    if depth not in (1, 2):
        raise ValueError("Depth must be 1 or 2")
    if entity_id not in {entity.id for entity in pack.entities}:
        raise KeyError(entity_id)
    visited = {entity_id}
    selected: set[str] = set()
    for _ in range(depth):
        frontier = set(visited)
        for claim in pack.claims:
            if claim.subject in frontier or claim.object in frontier:
                selected.add(claim.id)
                visited.update((claim.subject, claim.object))
    claims = [claim for claim in pack.claims if claim.id in selected]
    evidence_ids = {source_id for claim in claims for source_id in claim.evidence_ids}
    return Neighborhood(
        entities=[entity for entity in pack.entities if entity.id in visited],
        claims=claims,
        sources=[source for source in pack.sources if source.id in evidence_ids],
    )
