"""The searchable corpus: claims, measurements and sources as plain text records."""

from typing import Literal

from app.investigation import Investigation
from app.knowledge import Record
from app.normalisation.release import Release


class CorpusRecord(Record):
    ref: str  # kind:id, for example claim:O-C02 or measurement:<case>:<metric>:<n>
    kind: Literal["claim", "measurement", "source"]
    text: str
    entities: list[str]  # canonical entity IDs the record is about
    source_refs: list[str] = []  # the sources that back this record


class Corpus(Record):
    records: list[CorpusRecord]
    entity_names: dict[str, list[str]]  # canonical entity ID to the names it goes by


def build_corpus(investigations: list[Investigation], release: Release) -> Corpus:
    canonical = {
        (alias.case_id, alias.legacy_id): entity.canonical_id
        for entity in release.entities
        for alias in entity.aliases
    }
    entity_names = {entity.canonical_id: [entity.name] for entity in release.entities}
    records: list[CorpusRecord] = []
    for investigation in investigations:
        pack = investigation.pack
        names = {entity.id: entity.name for entity in pack.entities}
        for entity in pack.entities:
            entity_names[canonical[(pack.case_id, entity.id)]].append(entity.name)
        for claim in pack.claims:
            text = " ".join(
                [
                    claim.statement,
                    claim.caveat,
                    claim.predicate.replace("_", " "),
                    names[claim.subject],
                    names[claim.object],
                ]
            )
            ends = [
                canonical[(pack.case_id, claim.subject)],
                canonical[(pack.case_id, claim.object)],
            ]
            records.append(
                CorpusRecord(
                    ref=f"claim:{claim.id}",
                    kind="claim",
                    text=text,
                    entities=ends,
                    source_refs=[f"source:{source_id}" for source_id in claim.evidence_ids],
                )
            )
        for source in pack.sources:
            text = " ".join([source.title, source.publisher, source.locator, source.excerpt])
            records.append(
                CorpusRecord(ref=f"source:{source.id}", kind="source", text=text, entities=[])
            )
        metrics = {m.id: m for m in (pack.briefing.metrics if pack.briefing else [])}
        entity_by_canonical = {e.canonical_id: e.name for e in release.entities}
        for measurement in release.measurements:
            if measurement.case_id != pack.case_id:
                continue
            entity_name = entity_by_canonical.get(measurement.entity or "", "")
            text = " ".join(
                [
                    metrics[measurement.metric_id].title,
                    measurement.original_label,
                    measurement.value_text,
                    measurement.measure.replace("_", " "),
                    entity_name,
                ]
            )
            records.append(
                CorpusRecord(
                    ref=f"measurement:{measurement.id}",
                    kind="measurement",
                    text=text,
                    entities=[measurement.entity] if measurement.entity else [],
                    source_refs=[f"source:{s}" for s in metrics[measurement.metric_id].source_ids],
                )
            )
    return Corpus(records=records, entity_names=entity_names)
