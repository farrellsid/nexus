"""A normalisation release: the reviewed mapping of legacy records onto Nexus vocabularies.

A release is a projection beside the recorded claims, never an edit of them. `validate_release`
is a pure function: it proves the mapping covers the real packs exactly and uses only listed codes.
"""

from collections import Counter
from datetime import date, timedelta

from app.investigation import Investigation
from app.knowledge import Record
from app.normalisation.digest import fingerprint
from app.normalisation.vocabulary import Vocabulary

TEMPORAL_STATES = {"legacy_bounds", "unknown", "proposed_reinterpretation", "from_period_label"}


class Alias(Record):
    case_id: str
    legacy_id: str


class EntityRecord(Record):
    canonical_id: str
    name: str
    category: str
    subtype: str
    aliases: list[Alias]


class Temporal(Record):
    valid_kind: str
    valid_start: date | None
    valid_end_exclusive: date | None
    valid_at: date | None
    precision: str
    original_label: str | None
    statistic: str
    state: str


class ClaimRecord(Record):
    case_id: str
    claim_id: str
    predicate: str
    epistemic_status: str
    content_type: str
    modality: str
    release_status: str
    qualifiers: dict[str, str]
    temporal: Temporal
    needs_semantic_review: bool
    note: str | None


class SourceRecord(Record):
    case_id: str
    source_id: str
    publisher_class: str
    document_class: str
    legacy_reported_method: str | None


class MeasurementRecord(Record):
    id: str
    case_id: str
    metric_id: str
    point_index: int
    measure: str
    value_text: str
    entity: str | None
    original_label: str
    temporal: Temporal
    epistemic_status: str
    release_status: str
    claim_ids: list[str]
    note: str | None


class Release(Record):
    release_id: str
    vocabulary_version: str
    entities: list[EntityRecord]
    claims: list[ClaimRecord]
    sources: list[SourceRecord]
    measurements: list[MeasurementRecord]


def content_hash(release: Release) -> str:
    return fingerprint(release.model_dump(mode="json"))


def _coverage(kind: str, listed: list[str], real: set[str]) -> list[str]:
    problems = [f"{kind} {key} appears twice" for key, n in Counter(listed).items() if n > 1]
    problems += [f"missing {kind} {key}" for key in sorted(real - set(listed))]
    problems += [f"unknown {kind} {key}" for key in sorted(set(listed) - real)]
    return problems


def _claim_and_source_coverage(release: Release, investigations: list[Investigation]) -> list[str]:
    claims = {f"{i.pack.case_id}/{c.id}" for i in investigations for c in i.pack.claims}
    sources = {f"{i.pack.case_id}/{s.id}" for i in investigations for s in i.pack.sources}
    return _coverage(
        "claim", [f"{c.case_id}/{c.claim_id}" for c in release.claims], claims
    ) + _coverage("source", [f"{s.case_id}/{s.source_id}" for s in release.sources], sources)


def _entity_coverage(release: Release, investigations: list[Investigation]) -> list[str]:
    real = {f"{i.pack.case_id}/{e.id}" for i in investigations for e in i.pack.entities}
    problems = []
    canonical = [e.canonical_id for e in release.entities]
    problems += [
        f"canonical entity {k} appears twice" for k, n in Counter(canonical).items() if n > 1
    ]
    aliases = [f"{a.case_id}/{a.legacy_id}" for e in release.entities for a in e.aliases]
    problems += [f"alias {k} appears twice" for k, n in Counter(aliases).items() if n > 1]
    problems += [f"entity {k} has no canonical entity" for k in sorted(real - set(aliases))]
    problems += [f"unknown alias {k}" for k in sorted(set(aliases) - real)]
    return problems


def _measurement_coverage(
    release: Release,
    investigations: list[Investigation],
    metric_texts: dict[tuple[str, str], list[str]],
) -> list[str]:
    expected: dict[str, str] = {}
    for investigation in investigations:
        case_id = investigation.pack.case_id
        for metric in investigation.pack.briefing.metrics if investigation.pack.briefing else []:
            texts = metric_texts.get((case_id, metric.id), [])
            for index in range(len(metric.points)):
                expected[f"{case_id}:{metric.id}:{index}"] = (
                    texts[index] if index < len(texts) else ""
                )
    listed = [m.id for m in release.measurements]
    problems = _coverage("measurement", listed, set(expected))
    for measurement in release.measurements:
        original = expected.get(measurement.id)
        if original is not None and measurement.value_text != original:
            problems.append(
                f"measurement {measurement.id} value text {measurement.value_text!r} "
                f"differs from original {original!r}"
            )
    return problems


def _temporal_shape(label: str, t: Temporal, note: str | None) -> list[str]:
    problems = []
    if t.state not in TEMPORAL_STATES:
        problems.append(f"{label} has unknown temporal state {t.state!r}")
    if t.valid_kind == "interval":
        if not (t.valid_start and t.valid_end_exclusive and t.valid_start < t.valid_end_exclusive):
            problems.append(f"{label} interval must have a start before its exclusive end")
        if t.valid_at:
            problems.append(f"{label} interval must not carry valid_at")
    elif t.valid_kind == "instant":
        if not t.valid_at or t.valid_start or t.valid_end_exclusive:
            problems.append(f"{label} instant must carry valid_at only")
    elif t.valid_kind == "unknown" and (t.valid_at or t.valid_start or t.valid_end_exclusive):
        problems.append(f"{label} unknown validity must carry no dates")
    if t.state == "proposed_reinterpretation" and not (note or "").strip():
        problems.append(f"{label} reinterpretation needs a note")
    return problems


def _claim_temporal(release: Release, investigations: list[Investigation]) -> list[str]:
    stored = {
        f"{i.pack.case_id}/{c.id}": (c.valid_from, c.valid_to)
        for i in investigations
        for c in i.pack.claims
    }
    problems = []
    for record in release.claims:
        key = f"{record.case_id}/{record.claim_id}"
        t = record.temporal
        problems += _temporal_shape(f"claim {key}", t, record.note)
        start, end = stored.get(key, (None, None))
        if t.state == "unknown" and (start or end):
            problems.append(f"claim {key} has stored dates but is projected as unknown")
        if t.state == "legacy_bounds":
            matches = (
                t.valid_kind == "interval"
                and t.valid_start == start
                and end is not None
                and t.valid_end_exclusive == end + timedelta(days=1)
            )
            if not matches:
                problems.append(f"claim {key} legacy bounds do not match stored dates")
    return problems


def _codes(release: Release, vocabulary: Vocabulary) -> list[str]:
    problems = []

    def check(label: str, field: str, value: str, allowed) -> None:
        if value not in allowed:
            problems.append(f"{label} {field} {value!r} is not in the vocabulary")

    def status(label: str, value: str, note: str | None) -> None:
        check(label, "epistemic_status", value, vocabulary.epistemic_statuses)
        if value == "observed":
            problems.append(f"{label} uses observed, which vocabulary 1 assigns to nothing")
        if value == "forecast" and not (note or "").strip():
            problems.append(f"{label} forecast needs a note naming its issuer")

    def temporal(label: str, t: Temporal) -> None:
        check(label, "valid_kind", t.valid_kind, vocabulary.valid_kinds)
        check(label, "precision", t.precision, vocabulary.precisions)
        check(label, "statistic", t.statistic, vocabulary.statistics)

    for c in release.claims:
        label = f"claim {c.case_id}/{c.claim_id}"
        check(label, "predicate", c.predicate, vocabulary.predicates)
        check(label, "content_type", c.content_type, vocabulary.content_types)
        check(label, "modality", c.modality, vocabulary.modalities)
        check(label, "release_status", c.release_status, vocabulary.release_statuses)
        status(label, c.epistemic_status, c.note)
        temporal(label, c.temporal)
    for s in release.sources:
        label = f"source {s.case_id}/{s.source_id}"
        check(label, "publisher_class", s.publisher_class, vocabulary.publisher_classes)
        check(label, "document_class", s.document_class, vocabulary.document_classes)
    for m in release.measurements:
        label = f"measurement {m.id}"
        check(label, "measure", m.measure, vocabulary.measures)
        check(label, "release_status", m.release_status, vocabulary.release_statuses)
        status(label, m.epistemic_status, m.note)
        temporal(label, m.temporal)
        problems += _temporal_shape(label, m.temporal, m.note)
    for e in release.entities:
        allowed = vocabulary.entity_categories.get(e.category)
        if allowed is None:
            problems.append(
                f"entity {e.canonical_id} category {e.category!r} is not in the vocabulary"
            )
        elif e.subtype not in allowed:
            problems.append(
                f"entity {e.canonical_id} subtype {e.subtype!r} "
                f"does not belong to category {e.category!r}"
            )
    return problems


def validate_release(
    release: Release,
    vocabulary: Vocabulary,
    investigations: list[Investigation],
    metric_texts: dict[tuple[str, str], list[str]],
) -> list[str]:
    """Return every problem found; an empty list means the release is consistent."""
    problems: list[str] = []
    if release.vocabulary_version != vocabulary.version:
        problems.append(
            f"release uses vocabulary {release.vocabulary_version}, loaded {vocabulary.version}"
        )
    problems += _claim_and_source_coverage(release, investigations)
    problems += _entity_coverage(release, investigations)
    problems += _measurement_coverage(release, investigations, metric_texts)
    problems += _codes(release, vocabulary)
    problems += _claim_temporal(release, investigations)
    return problems
