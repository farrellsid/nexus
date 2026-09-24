"""Knowledge-owned PostgreSQL operations for the acquisition log.

Every write is one locked transaction and appends; nothing is edited. The database holds hashes and
outcomes, never fetched bytes. Nothing here touches sources, claims, proposals or releases.
"""

from datetime import datetime
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from app.acquisition.extraction import TextExtraction
from app.acquisition.fetch import TOOL, FetchResult
from app.acquisition.verification import Verification
from app.knowledge import Record
from app.review import ReviewConflict
from app.storage.database import Database

CURRENT_BASELINE = (
    "SELECT b.* FROM source_baseline b WHERE b.source_id = %s"
    " AND NOT EXISTS (SELECT 1 FROM source_baseline n WHERE n.supersedes_id = b.id)"
)


class AttemptRow(Record):
    id: UUID
    source_id: str
    requested_url: str
    final_url: str
    started_at: datetime
    status: int | None
    content_type: str | None
    byte_count: int
    outcome: str
    error: str | None
    sha256: str | None
    stored: bool


class BaselineRow(Record):
    id: UUID
    source_id: str
    sha256: str
    text_sha256: str | None
    basis: str
    reviewer: str
    supersedes_id: UUID | None


class VerificationRow(Record):
    id: UUID
    source_id: str
    attempt_id: UUID
    baseline_id: UUID | None
    state: str
    reason: str
    comparison_readiness: str
    byte_match: bool | None
    text_match: bool | None
    passages: list[dict]


class PostgresAcquisition:
    def __init__(self, database: Database):
        self.database = database

    def _lock(self, connection) -> None:
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))", (self.database.schema + "acq",)
        )

    @staticmethod
    def _require_source(connection, source_id: str) -> None:
        if not connection.execute(
            "SELECT 1 FROM evidence_sources WHERE id = %s", (source_id,)
        ).fetchone():
            raise KeyError(source_id)

    def log_attempt(self, source_id: str, result: FetchResult, stored: bool) -> UUID:
        """Append one attempt, whatever its outcome, and record any content it produced."""
        identity = uuid4()
        with self.database.connect() as connection:
            self._lock(connection)
            self._require_source(connection, source_id)
            if result.sha256:
                connection.execute(
                    "INSERT INTO content_object(sha256, size, media_type, first_captured_at)"
                    " VALUES (%s, %s, %s, %s) ON CONFLICT (sha256) DO NOTHING",
                    (result.sha256, result.byte_count, result.content_type, result.ended_at),
                )
            connection.execute(
                "INSERT INTO fetch_attempt(id, source_id, requested_url, final_url, redirect_chain,"
                " started_at, ended_at, status, content_type, etag, last_modified, byte_count,"
                " tool, outcome, error, sha256, stored)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    identity,
                    source_id,
                    result.source_url,
                    result.final_url,
                    Jsonb(result.redirect_chain),
                    result.started_at,
                    result.ended_at,
                    result.status,
                    result.content_type,
                    result.etag,
                    result.last_modified,
                    result.byte_count,
                    TOOL,
                    result.outcome,
                    result.error,
                    result.sha256,
                    stored,
                ),
            )
        return identity

    def attempts(self, source_id: str) -> list[AttemptRow]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, source_id, requested_url, final_url, started_at, status, content_type,"
                " byte_count, outcome, error, sha256, stored FROM fetch_attempt"
                " WHERE source_id = %s ORDER BY started_at, id",
                (source_id,),
            ).fetchall()
        return [AttemptRow(**row) for row in rows]

    def set_baseline(
        self,
        source_id: str,
        sha256: str,
        text_sha256: str | None,
        basis: str,
        reviewer: str,
        supersedes: UUID | None = None,
    ) -> UUID:
        """Name the content a source is compared with. A later baseline must supersede the first."""
        identity = uuid4()
        with self.database.connect() as connection:
            self._lock(connection)
            self._require_source(connection, source_id)
            if not connection.execute(
                "SELECT 1 FROM content_object WHERE sha256 = %s", (sha256,)
            ).fetchone():
                raise KeyError(sha256)
            current = connection.execute(CURRENT_BASELINE, (source_id,)).fetchone()
            if current and supersedes != current["id"]:
                raise ReviewConflict("This source has a current baseline; name it in `supersedes`")
            if not current and supersedes is not None:
                raise ReviewConflict("There is no current baseline to supersede")
            connection.execute(
                "INSERT INTO source_baseline"
                "(id, source_id, sha256, text_sha256, basis, reviewer, supersedes_id)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (identity, source_id, sha256, text_sha256, basis, reviewer, supersedes),
            )
        return identity

    def current_baseline(self, source_id: str) -> BaselineRow | None:
        with self.database.connect() as connection:
            row = connection.execute(CURRENT_BASELINE, (source_id,)).fetchone()
        if row is None:
            return None
        return BaselineRow(**{key: row[key] for key in BaselineRow.model_fields if key in row})

    def record_extraction(self, sha256: str, extraction: TextExtraction) -> UUID:
        """Record an extraction of stored content; idempotent for the same extractor."""
        with self.database.connect() as connection:
            self._lock(connection)
            if not connection.execute(
                "SELECT 1 FROM content_object WHERE sha256 = %s", (sha256,)
            ).fetchone():
                raise KeyError(sha256)
            existing = connection.execute(
                "SELECT id FROM extraction_version WHERE sha256 = %s AND extractor = %s",
                (sha256, extraction.extractor),
            ).fetchone()
            if existing:
                return existing["id"]
            identity = uuid4()
            connection.execute(
                "INSERT INTO extraction_version(id, sha256, extractor, text_sha256, readable)"
                " VALUES (%s, %s, %s, %s, %s)",
                (
                    identity,
                    sha256,
                    extraction.extractor,
                    extraction.text_sha256,
                    extraction.readable,
                ),
            )
        return identity

    def extraction_text_hash(self, sha256: str) -> str | None:
        """The text hash of the latest extraction of this content, if one was recorded."""
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT text_sha256 FROM extraction_version WHERE sha256 = %s"
                " ORDER BY created_at DESC, id LIMIT 1",
                (sha256,),
            ).fetchone()
        return row["text_sha256"] if row else None

    def record_verification(
        self,
        source_id: str,
        attempt_id: UUID,
        baseline_id: UUID | None,
        verification: Verification,
    ) -> UUID:
        identity = uuid4()
        with self.database.connect() as connection:
            self._lock(connection)
            self._require_source(connection, source_id)
            connection.execute(
                "INSERT INTO verification_result(id, source_id, attempt_id, baseline_id, state,"
                " reason, comparison_readiness, byte_match, text_match, passages)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    identity,
                    source_id,
                    attempt_id,
                    baseline_id,
                    verification.state,
                    verification.reason,
                    verification.comparison_readiness,
                    verification.byte_match,
                    verification.text_match,
                    Jsonb([p.model_dump() for p in verification.passages]),
                ),
            )
        return identity

    def verifications(self, source_id: str) -> list[VerificationRow]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, source_id, attempt_id, baseline_id, state, reason,"
                " comparison_readiness, byte_match, text_match, passages FROM verification_result"
                " WHERE source_id = %s ORDER BY checked_at, id",
                (source_id,),
            ).fetchall()
        return [VerificationRow(**row) for row in rows]
