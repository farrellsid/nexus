"""Knowledge-owned PostgreSQL operations. Each write is one locked transaction."""

import hashlib
import json
from uuid import NAMESPACE_URL, UUID, uuid5

from psycopg.types.json import Jsonb

from app.investigation import Investigation
from app.knowledge import Claim
from app.review import (
    AcceptedVersion,
    Decision,
    DecisionRequest,
    Proposal,
    ProposalRequest,
    ReviewConflict,
    ReviewHistory,
)
from app.storage.database import Database


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def seed_payload(investigation: Investigation) -> dict:
    """Return the claim-review seed, excluding separately managed geography."""
    payload = investigation.model_dump(mode="json")
    payload.pop("geography", None)
    # Preserve the original copper seed's canonical shape after optional
    # briefing and location metadata were added for later investigations.
    if payload["pack"]["briefing"] is None:
        del payload["pack"]["briefing"]
        for entity in payload["pack"]["entities"]:
            entity.pop("location_precision", None)
    return payload


class PostgresReviews:
    def __init__(self, database: Database):
        self.database = database

    def initialize(self, investigation: Investigation) -> None:
        """Import candidates exactly once. Changed fixtures require explicit migration."""
        payload = seed_payload(investigation)
        digest = fingerprint(payload)
        with self.database.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (self.database.schema,)
            )
            existing = connection.execute(
                "SELECT fingerprint FROM investigation_seed WHERE case_id = %s",
                (investigation.pack.case_id,),
            ).fetchone()
            if existing:
                if existing["fingerprint"] != digest:
                    raise RuntimeError(
                        "Fixture differs from the retained database seed; migrate explicitly"
                    )
                return
            connection.execute(
                "INSERT INTO investigation_seed(case_id, fingerprint, payload) VALUES (%s, %s, %s)",
                (investigation.pack.case_id, digest, Jsonb(payload)),
            )
            for source in investigation.pack.sources:
                source_data = source.model_dump(mode="json")
                connection.execute(
                    "INSERT INTO evidence_sources(id, payload, content_hash) VALUES (%s, %s, %s)",
                    (source.id, Jsonb(source_data), fingerprint(source_data)),
                )
            for claim in investigation.pack.claims:
                connection.execute(
                    "INSERT INTO knowledge_assertions(id, case_id) VALUES (%s, %s)",
                    (claim.id, investigation.pack.case_id),
                )
                proposal_id = uuid5(NAMESPACE_URL, f"nexus:{investigation.pack.case_id}:{claim.id}")
                self._insert_proposal(
                    connection,
                    proposal_id,
                    claim,
                    0,
                    "Research fixture import",
                    "Imported as a candidate; application review has not occurred.",
                    digest,
                )

    def _insert_proposal(self, connection, proposal_id, claim, base, author, reason, digest):
        connection.execute(
            """
            INSERT INTO knowledge_proposals
                (id, claim_id, base_revision, payload, author, reason, request_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            (
                proposal_id,
                claim.id,
                base,
                Jsonb(claim.model_dump(mode="json")),
                author,
                reason,
                digest,
            ),
        )
        for source_id in claim.evidence_ids:
            connection.execute(
                "INSERT INTO knowledge_proposal_evidence(proposal_id, source_id) VALUES (%s, %s)",
                (proposal_id, source_id),
            )

    def _head(self, connection, claim_id, lock=False):
        query = "SELECT current_revision FROM knowledge_assertions WHERE id = %s"
        row = connection.execute(query + (" FOR UPDATE" if lock else ""), (claim_id,)).fetchone()
        if row is None:
            raise KeyError(claim_id)
        return row["current_revision"]

    def _history(self, connection, claim_id):
        revision = self._head(connection, claim_id)
        rows = connection.execute(
            """
            SELECT p.*, d.request_id, d.decision, d.reviewer, d.reason AS review_reason,
                   d.recorded_at AS reviewed_at
            FROM knowledge_proposals p LEFT JOIN knowledge_decisions d ON d.proposal_id = p.id
            WHERE p.claim_id = %s ORDER BY p.proposed_at, p.id
        """,
            (claim_id,),
        ).fetchall()
        versions = connection.execute(
            """
            SELECT * FROM knowledge_versions WHERE claim_id = %s ORDER BY revision
        """,
            (claim_id,),
        ).fetchall()
        return ReviewHistory(
            claim_id=claim_id,
            current_revision=revision,
            proposals=[
                Proposal(
                    id=row["id"],
                    claim_id=claim_id,
                    base_revision=row["base_revision"],
                    claim=Claim.model_validate(row["payload"]),
                    author=row["author"],
                    reason=row["reason"],
                    proposed_at=row["proposed_at"],
                    decision=Decision(
                        request_id=row["request_id"],
                        decision=row["decision"],
                        reviewer=row["reviewer"],
                        reason=row["review_reason"],
                        recorded_at=row["reviewed_at"],
                    )
                    if row["decision"]
                    else None,
                )
                for row in rows
            ],
            versions=[
                AcceptedVersion(
                    revision=row["revision"],
                    proposal_id=row["proposal_id"],
                    claim=Claim.model_validate(row["payload"]),
                    recorded_at=row["recorded_at"],
                )
                for row in versions
            ],
        )

    def history(self, claim_id: str) -> ReviewHistory:
        with self.database.connect() as connection:
            # A history read must not mix a head from before a concurrent acceptance
            # with versions from after it.
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            return self._history(connection, claim_id)

    def propose(self, claim: Claim, request: ProposalRequest) -> ReviewHistory:
        digest = fingerprint({"claim_id": claim.id, **request.model_dump(mode="json")})
        with self.database.connect() as connection:
            revision = self._head(connection, claim.id, lock=True)
            existing = connection.execute(
                "SELECT claim_id, request_hash FROM knowledge_proposals WHERE id = %s",
                (request.request_id,),
            ).fetchone()
            if existing:
                if existing["request_hash"] != digest:
                    raise ReviewConflict("Request ID was already used for a different proposal")
                return self._history(connection, claim.id)
            if revision != request.base_revision:
                raise ReviewConflict(
                    "Baseline changed. Reload the claim before proposing a correction."
                )
            self._insert_proposal(
                connection,
                request.request_id,
                claim,
                revision,
                request.author,
                request.reason,
                digest,
            )
            return self._history(connection, claim.id)

    def decide(self, proposal_id: UUID, request: DecisionRequest) -> ReviewHistory:
        digest = fingerprint({"proposal_id": str(proposal_id), **request.model_dump(mode="json")})
        with self.database.connect() as connection:
            proposal = connection.execute(
                "SELECT * FROM knowledge_proposals WHERE id = %s",
                (proposal_id,),
            ).fetchone()
            if proposal is None:
                raise KeyError(str(proposal_id))
            claim_id = proposal["claim_id"]
            revision = self._head(connection, claim_id, lock=True)
            existing = connection.execute(
                "SELECT request_hash FROM knowledge_decisions WHERE request_id = %s",
                (request.request_id,),
            ).fetchone()
            if existing:
                if existing["request_hash"] != digest:
                    raise ReviewConflict("Request ID was already used for a different review")
                return self._history(connection, claim_id)
            if connection.execute(
                "SELECT 1 FROM knowledge_decisions WHERE proposal_id = %s",
                (proposal_id,),
            ).fetchone():
                raise ReviewConflict("This proposal has already been reviewed. Reload its history.")
            if revision != request.expected_revision:
                raise ReviewConflict("Baseline changed. Reload the claim before reviewing.")
            if request.decision == "accept" and proposal["base_revision"] != revision:
                raise ReviewConflict(
                    "This proposal is stale. Propose a new correction against the current baseline."
                )
            connection.execute(
                """
                INSERT INTO knowledge_decisions
                    (proposal_id, request_id, decision, reviewer, reason, request_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    proposal_id,
                    request.request_id,
                    request.decision,
                    request.reviewer,
                    request.reason,
                    digest,
                ),
            )
            if request.decision == "accept":
                accepted = Claim.model_validate(proposal["payload"]).model_copy(
                    update={"review_status": "accepted", "ground_truth": False},
                )
                connection.execute(
                    """
                    INSERT INTO knowledge_versions(claim_id, revision, proposal_id, payload)
                    VALUES (%s, %s, %s, %s)
                """,
                    (claim_id, revision + 1, proposal_id, Jsonb(accepted.model_dump(mode="json"))),
                )
                connection.execute(
                    "UPDATE knowledge_assertions SET current_revision = %s WHERE id = %s",
                    (revision + 1, claim_id),
                )
            return self._history(connection, claim_id)

    def current_claims(self, claim_ids: list[str] | None = None) -> list[Claim]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT ON (a.id) a.id, v.payload AS accepted,
                       p.payload AS candidate, d.decision
                FROM knowledge_assertions a
                JOIN knowledge_proposals p ON p.claim_id = a.id
                LEFT JOIN knowledge_decisions d ON d.proposal_id = p.id
                LEFT JOIN knowledge_versions v
                    ON v.claim_id = a.id AND v.revision = a.current_revision
                WHERE (%s::text[] IS NULL OR a.id = ANY(%s::text[]))
                ORDER BY a.id, p.proposed_at, p.id
            """,
                (claim_ids, claim_ids),
            ).fetchall()
            claims = []
            for row in rows:
                claim = Claim.model_validate(row["accepted"] or row["candidate"])
                if row["accepted"] is None and row["decision"] == "reject":
                    claim = claim.model_copy(update={"review_status": "rejected"})
                claims.append(claim)
            return claims
