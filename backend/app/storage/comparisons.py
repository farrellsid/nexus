"""Knowledge-owned PostgreSQL operations for comparability judgements.

Every write is one locked transaction. A judgement is never edited: a later one supersedes it by
naming it. Nothing here touches claims, proposals, decisions, versions or normalisation releases.
"""

from typing import Literal
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from app.comparability.display import ComparisonDisplay, build_display
from app.comparability.model import Membership, Relation
from app.comparability.reports import build_reports
from app.investigation import Investigation
from app.knowledge import Record
from app.normalisation.vocabulary import Vocabulary
from app.review import ReviewConflict
from app.storage.database import Database
from app.storage.normalisation import PostgresNormalisation

Assessment = Literal["comparable", "not_comparable", "unresolved"]
RelationKind = Literal["contradicts", "revises", "duplicates_origin", "different_scope", "supports"]
CURRENT = (
    "SELECT m.* FROM comparison_membership m WHERE m.set_id = %s"
    " AND NOT EXISTS (SELECT 1 FROM comparison_membership n WHERE n.supersedes_id = m.id)"
)


class ComparisonSet(Record):
    set_id: str
    definition_version: str
    display: ComparisonDisplay


class PostgresComparisons:
    def __init__(self, database: Database, normalisation: PostgresNormalisation):
        self.database = database
        self.normalisation = normalisation

    def _lock(self, connection) -> None:
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", (self.database.schema + "cmp",)
        )

    def create_set(self, set_id: str, definition_version: str, key: dict) -> None:
        with self.database.connect() as connection:
            self._lock(connection)
            existing = connection.execute(
                "SELECT definition_version, comparison_key FROM comparison_set WHERE id = %s",
                (set_id,),
            ).fetchone()
            if existing:
                if (existing["definition_version"], existing["comparison_key"]) != (
                    definition_version,
                    key,
                ):
                    raise ReviewConflict(f"Comparison set {set_id} exists with different content")
                return
            connection.execute(
                "INSERT INTO comparison_set(id, definition_version, comparison_key)"
                " VALUES (%s, %s, %s)",
                (set_id, definition_version, Jsonb(key)),
            )

    def assess(
        self,
        set_id: str,
        report_id: str,
        assessment: Assessment,
        reason: str,
        reviewer: str,
        supersedes: UUID | None = None,
    ) -> UUID:
        """Record a reviewer's judgement; a later judgement must name the one it supersedes."""
        accepted = self.normalisation.accepted_release_id()
        with self.database.connect() as connection:
            self._lock(connection)
            if not connection.execute(
                "SELECT 1 FROM comparison_set WHERE id = %s", (set_id,)
            ).fetchone():
                raise KeyError(set_id)
            if (
                accepted is None
                or not connection.execute(
                    "SELECT 1 FROM measurement WHERE release_id = %s AND id = %s",
                    (accepted, report_id),
                ).fetchone()
            ):
                raise KeyError(report_id)
            current = connection.execute(
                CURRENT + " AND m.report_id = %s", (set_id, report_id)
            ).fetchone()
            if current and supersedes != current["id"]:
                raise ReviewConflict(
                    "This report already has a current judgement; name it in `supersedes`"
                )
            if not current and supersedes is not None:
                raise ReviewConflict("There is no current judgement to supersede")
            identity = uuid4()
            connection.execute(
                "INSERT INTO comparison_membership"
                "(id, set_id, report_id, assessment, reason, reviewer, supersedes_id)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (identity, set_id, report_id, assessment, reason, reviewer, supersedes),
            )
            return identity

    def relate(
        self,
        left_ref: str,
        right_ref: str,
        relation: RelationKind,
        rationale: str,
        reviewer: str,
        evidence_refs: tuple[str, ...] = (),
    ) -> UUID:
        identity = uuid4()
        with self.database.connect() as connection:
            self._lock(connection)
            connection.execute(
                "INSERT INTO claim_relation"
                "(id, left_ref, right_ref, relation, rationale, evidence_refs, reviewer)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    identity,
                    left_ref,
                    right_ref,
                    relation,
                    rationale,
                    Jsonb(list(evidence_refs)),
                    reviewer,
                ),
            )
        return identity

    def displays(
        self, investigations: list[Investigation], vocabulary: Vocabulary
    ) -> list[ComparisonSet]:
        reports = {
            report.id: report
            for report in build_reports(
                self.normalisation.measurements(), investigations, vocabulary
            )
        }
        shown: list[ComparisonSet] = []
        with self.database.connect() as connection:
            sets = connection.execute(
                "SELECT id, definition_version FROM comparison_set ORDER BY id"
            ).fetchall()
            relations = connection.execute(
                "SELECT left_ref, right_ref, relation, rationale, reviewer FROM claim_relation"
                " ORDER BY recorded_at, id"
            ).fetchall()
            for row in sets:
                memberships = [
                    Membership(
                        report_id=m["report_id"],
                        assessment=m["assessment"],
                        reason=m["reason"],
                        reviewer=m["reviewer"],
                    )
                    for m in connection.execute(CURRENT + " ORDER BY m.report_id", (row["id"],))
                ]
                ids = {m.report_id for m in memberships}
                related = [
                    Relation(
                        left=r["left_ref"].removeprefix("measurement:"),
                        right=r["right_ref"].removeprefix("measurement:"),
                        relation=r["relation"],
                        rationale=r["rationale"],
                        reviewer=r["reviewer"],
                    )
                    for r in relations
                    if r["left_ref"].removeprefix("measurement:") in ids
                    and r["right_ref"].removeprefix("measurement:") in ids
                ]
                members = [reports[i] for i in sorted(ids) if i in reports]
                shown.append(
                    ComparisonSet(
                        set_id=row["id"],
                        definition_version=row["definition_version"],
                        display=build_display(members, memberships, related),
                    )
                )
        return shown

    def display(
        self, set_id: str, investigations: list[Investigation], vocabulary: Vocabulary
    ) -> ComparisonSet | None:
        return next(
            (s for s in self.displays(investigations, vocabulary) if s.set_id == set_id), None
        )
