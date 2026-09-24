"""Knowledge-owned PostgreSQL operations for normalisation releases.

Recording a release never touches claims, proposals, decisions or versions. A release becomes
readable only after an accept decision; the latest accepted release is the one served.
"""

from typing import Literal
from uuid import UUID

from psycopg.types.json import Jsonb

from app.knowledge import Record
from app.normalisation.release import (
    Alias,
    ClaimRecord,
    EntityRecord,
    MeasurementRecord,
    Release,
    Temporal,
    content_hash,
)
from app.normalisation.vocabulary import Vocabulary
from app.review import ReviewConflict
from app.storage.database import Database

TEMPORAL_COLUMNS = (
    "valid_kind, valid_start, valid_end_exclusive, valid_at, precision, temporal_label, "
    "statistic, time_state"
)


class ClaimProjection(Record):
    release_id: str
    basis_proposal_id: UUID
    claim: ClaimRecord


def _temporal(row) -> Temporal:
    return Temporal(
        valid_kind=row["valid_kind"],
        valid_start=row["valid_start"],
        valid_end_exclusive=row["valid_end_exclusive"],
        valid_at=row["valid_at"],
        precision=row["precision"],
        original_label=row["temporal_label"],
        statistic=row["statistic"],
        state=row["time_state"],
    )


def _temporal_values(t: Temporal) -> tuple:
    return (
        t.valid_kind,
        t.valid_start,
        t.valid_end_exclusive,
        t.valid_at,
        t.precision,
        t.original_label,
        t.statistic,
        t.state,
    )


class PostgresNormalisation:
    def __init__(self, database: Database):
        self.database = database

    def record_release(self, release: Release, vocabulary: Vocabulary) -> str:
        """Store a release for review. Idempotent for identical content."""
        digest = content_hash(release)
        with self.database.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (self.database.schema + "norm",)
            )
            self._record_vocabulary(connection, vocabulary)
            existing = connection.execute(
                "SELECT content_hash FROM normalisation_release WHERE id = %s",
                (release.release_id,),
            ).fetchone()
            if existing:
                if existing["content_hash"] != digest:
                    raise ReviewConflict(
                        f"Release {release.release_id} exists with different content"
                    )
                return release.release_id
            twin = connection.execute(
                "SELECT id FROM normalisation_release WHERE content_hash = %s", (digest,)
            ).fetchone()
            if twin:
                raise ReviewConflict(f"This content is already recorded as {twin['id']}")
            self._require_continuity(connection, release)
            connection.execute(
                "INSERT INTO normalisation_release(id, vocabulary_version, content_hash, payload)"
                " VALUES (%s, %s, %s, %s)",
                (
                    release.release_id,
                    release.vocabulary_version,
                    digest,
                    Jsonb(release.model_dump(mode="json")),
                ),
            )
            self._insert_children(connection, release)
        return release.release_id

    def _record_vocabulary(self, connection, vocabulary: Vocabulary) -> None:
        digest = vocabulary.content_hash()
        row = connection.execute(
            "SELECT content_hash FROM vocabulary_release WHERE version = %s",
            (vocabulary.version,),
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO vocabulary_release(version, content_hash, definition)"
                " VALUES (%s, %s, %s)",
                (vocabulary.version, digest, Jsonb(vocabulary.model_dump(mode="json"))),
            )
        elif row["content_hash"] != digest:
            raise ReviewConflict(f"Vocabulary {vocabulary.version} exists with different content")

    def _require_continuity(self, connection, release: Release) -> None:
        """A new release must keep every canonical ID and alias of the latest accepted one."""
        latest = self._accepted_id(connection)
        if latest is None:
            return
        entities = connection.execute(
            "SELECT canonical_id FROM entity_registry WHERE release_id = %s", (latest,)
        ).fetchall()
        aliases = connection.execute(
            "SELECT case_id, legacy_id, canonical_id FROM entity_alias WHERE release_id = %s",
            (latest,),
        ).fetchall()
        kept = {e.canonical_id for e in release.entities}
        mapping = {
            (a.case_id, a.legacy_id): e.canonical_id for e in release.entities for a in e.aliases
        }
        for row in entities:
            if row["canonical_id"] not in kept:
                raise ReviewConflict(f"Release drops accepted entity {row['canonical_id']}")
        for row in aliases:
            if mapping.get((row["case_id"], row["legacy_id"])) != row["canonical_id"]:
                raise ReviewConflict(
                    f"Release drops or repoints accepted alias {row['case_id']}/{row['legacy_id']}"
                    f" of {row['canonical_id']}"
                )

    def _insert_children(self, connection, release: Release) -> None:
        rid = release.release_id
        for entity in release.entities:
            connection.execute(
                "INSERT INTO entity_registry(release_id, canonical_id, name, category, subtype)"
                " VALUES (%s, %s, %s, %s, %s)",
                (rid, entity.canonical_id, entity.name, entity.category, entity.subtype),
            )
            for alias in entity.aliases:
                connection.execute(
                    "INSERT INTO entity_alias(release_id, case_id, legacy_id, canonical_id)"
                    " VALUES (%s, %s, %s, %s)",
                    (rid, alias.case_id, alias.legacy_id, entity.canonical_id),
                )
        for claim in release.claims:
            basis = connection.execute(
                "SELECT id FROM knowledge_proposals WHERE claim_id = %s"
                " ORDER BY proposed_at, id LIMIT 1",
                (claim.claim_id,),
            ).fetchone()
            if basis is None:
                raise KeyError(claim.claim_id)
            connection.execute(
                "INSERT INTO claim_projection(release_id, claim_id, case_id, basis_proposal_id,"
                " predicate, epistemic_status, content_type, modality, release_status, qualifiers,"
                f" {TEMPORAL_COLUMNS}, needs_semantic_review, note)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
                " %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    rid,
                    claim.claim_id,
                    claim.case_id,
                    basis["id"],
                    claim.predicate,
                    claim.epistemic_status,
                    claim.content_type,
                    claim.modality,
                    claim.release_status,
                    Jsonb(claim.qualifiers),
                    *_temporal_values(claim.temporal),
                    claim.needs_semantic_review,
                    claim.note,
                ),
            )
        for source in release.sources:
            connection.execute(
                "INSERT INTO source_classification(release_id, source_id, case_id, publisher_class,"
                " document_class, legacy_reported_method) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    rid,
                    source.source_id,
                    source.case_id,
                    source.publisher_class,
                    source.document_class,
                    source.legacy_reported_method,
                ),
            )
        for m in release.measurements:
            connection.execute(
                "INSERT INTO measurement(release_id, id, case_id, metric_id, point_index, measure,"
                " value_text, entity, original_label, "
                f"{TEMPORAL_COLUMNS}, epistemic_status, release_status, claim_ids, note)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,"
                " %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    rid,
                    m.id,
                    m.case_id,
                    m.metric_id,
                    m.point_index,
                    m.measure,
                    m.value_text,
                    m.entity,
                    m.original_label,
                    *_temporal_values(m.temporal),
                    m.epistemic_status,
                    m.release_status,
                    m.claim_ids,
                    m.note,
                ),
            )

    def decide(
        self,
        release_id: str,
        decision: Literal["accept", "reject"],
        reviewer: str,
        reason: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (self.database.schema + "norm",)
            )
            if not connection.execute(
                "SELECT 1 FROM normalisation_release WHERE id = %s", (release_id,)
            ).fetchone():
                raise KeyError(release_id)
            existing = connection.execute(
                "SELECT decision, reviewer, reason FROM normalisation_decision"
                " WHERE release_id = %s",
                (release_id,),
            ).fetchone()
            if existing:
                if (existing["decision"], existing["reviewer"], existing["reason"]) == (
                    decision,
                    reviewer,
                    reason,
                ):
                    return
                raise ReviewConflict(f"Release {release_id} already has a decision")
            connection.execute(
                "INSERT INTO normalisation_decision(release_id, decision, reviewer, reason)"
                " VALUES (%s, %s, %s, %s)",
                (release_id, decision, reviewer, reason),
            )

    @staticmethod
    def _accepted_id(connection) -> str | None:
        row = connection.execute(
            "SELECT release_id FROM normalisation_decision WHERE decision = 'accept'"
            " ORDER BY recorded_at DESC, release_id DESC LIMIT 1"
        ).fetchone()
        return row["release_id"] if row else None

    def accepted_release_id(self) -> str | None:
        with self.database.connect() as connection:
            return self._accepted_id(connection)

    def claim_projection(self, claim_id: str) -> ClaimProjection | None:
        with self.database.connect() as connection:
            release_id = self._accepted_id(connection)
            row = (
                connection.execute(
                    "SELECT * FROM claim_projection WHERE release_id = %s AND claim_id = %s",
                    (release_id, claim_id),
                ).fetchone()
                if release_id
                else None
            )
        if row is None:
            return None
        return ClaimProjection(
            release_id=row["release_id"],
            basis_proposal_id=row["basis_proposal_id"],
            claim=ClaimRecord(
                case_id=row["case_id"],
                claim_id=row["claim_id"],
                predicate=row["predicate"],
                epistemic_status=row["epistemic_status"],
                content_type=row["content_type"],
                modality=row["modality"],
                release_status=row["release_status"],
                qualifiers=row["qualifiers"],
                temporal=_temporal(row),
                needs_semantic_review=row["needs_semantic_review"],
                note=row["note"],
            ),
        )

    def resolve_alias(self, case_id: str, legacy_id: str) -> EntityRecord | None:
        with self.database.connect() as connection:
            release_id = self._accepted_id(connection)
            if release_id is None:
                return None
            entity = connection.execute(
                "SELECT r.* FROM entity_alias a JOIN entity_registry r"
                " ON r.release_id = a.release_id AND r.canonical_id = a.canonical_id"
                " WHERE a.release_id = %s AND a.case_id = %s AND a.legacy_id = %s",
                (release_id, case_id, legacy_id),
            ).fetchone()
            if entity is None:
                return None
            aliases = connection.execute(
                "SELECT case_id, legacy_id FROM entity_alias"
                " WHERE release_id = %s AND canonical_id = %s ORDER BY case_id, legacy_id",
                (release_id, entity["canonical_id"]),
            ).fetchall()
        return EntityRecord(
            canonical_id=entity["canonical_id"],
            name=entity["name"],
            category=entity["category"],
            subtype=entity["subtype"],
            aliases=[Alias(case_id=a["case_id"], legacy_id=a["legacy_id"]) for a in aliases],
        )

    def measurements(self, entity: str | None = None) -> list[MeasurementRecord]:
        with self.database.connect() as connection:
            release_id = self._accepted_id(connection)
            if release_id is None:
                return []
            rows = connection.execute(
                "SELECT * FROM measurement WHERE release_id = %s"
                " AND (%s::text IS NULL OR entity = %s)"
                " ORDER BY case_id, metric_id, point_index",
                (release_id, entity, entity),
            ).fetchall()
        return [
            MeasurementRecord(
                id=row["id"],
                case_id=row["case_id"],
                metric_id=row["metric_id"],
                point_index=row["point_index"],
                measure=row["measure"],
                value_text=row["value_text"],
                entity=row["entity"],
                original_label=row["original_label"],
                temporal=_temporal(row),
                epistemic_status=row["epistemic_status"],
                release_status=row["release_status"],
                claim_ids=row["claim_ids"],
                note=row["note"],
            )
            for row in rows
        ]
