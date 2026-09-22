"""Review contracts and rules, independent of storage and HTTP.

Acceptance is a local editorial decision, never a claim of physical verification.
Corrections change the accepted baseline only after a separate review decision.
"""

from datetime import date, datetime
from typing import Annotated, Literal, Protocol
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from app.evidence import validate_references
from app.knowledge import Claim, EvidencePack, Record

Nonblank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
Reviewer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ReviewConflict(Exception):
    """The displayed baseline or request identity no longer matches stored state."""


class ProposalRequest(Record):
    request_id: UUID
    base_revision: int = Field(ge=0)
    statement: Nonblank
    caveat: Nonblank
    evidence_ids: list[str] = Field(min_length=1, max_length=30)
    valid_from: date | None = None
    valid_to: date | None = None
    author: Reviewer
    reason: Nonblank

    @model_validator(mode="after")
    def validate_dates(self) -> "ProposalRequest":
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("Valid from must not be later than valid to")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("Evidence references must be unique")
        return self


class DecisionRequest(Record):
    request_id: UUID
    expected_revision: int = Field(ge=0)
    decision: Literal["accept", "reject"]
    reviewer: Reviewer
    reason: Nonblank


class Decision(Record):
    request_id: UUID
    decision: Literal["accept", "reject"]
    reviewer: str
    reason: str
    recorded_at: datetime


class Proposal(Record):
    id: UUID
    claim_id: str
    base_revision: int
    claim: Claim
    author: str
    reason: str
    proposed_at: datetime
    decision: Decision | None = None


class AcceptedVersion(Record):
    revision: int
    proposal_id: UUID
    claim: Claim
    recorded_at: datetime


class ReviewHistory(Record):
    claim_id: str
    current_revision: int
    proposals: list[Proposal]
    versions: list[AcceptedVersion]


class ReviewAvailability(Record):
    enabled: bool
    mode: Literal["postgresql", "read_only_fixture"]


class ReviewRepository(Protocol):
    def history(self, claim_id: str) -> ReviewHistory: ...
    def propose(self, claim: Claim, request: ProposalRequest) -> ReviewHistory: ...
    def decide(self, proposal_id: UUID, request: DecisionRequest) -> ReviewHistory: ...
    def current_claims(self) -> list[Claim]: ...


class ReviewService:
    def __init__(self, pack: EvidencePack, repository: ReviewRepository):
        self.pack = pack
        self.repository = repository

    def propose(self, claim_id: str, request: ProposalRequest) -> ReviewHistory:
        original = next((claim for claim in self.pack.claims if claim.id == claim_id), None)
        if original is None:
            raise KeyError(claim_id)
        validate_references(request.evidence_ids, self.pack.sources)
        # Identity, relation, source labels and original fixture-recorded date stay intact.
        # Proposal/review acquisition time is stored separately by PostgreSQL.
        claim = original.model_copy(
            update={
                "statement": request.statement,
                "caveat": request.caveat,
                "evidence_ids": request.evidence_ids,
                "valid_from": request.valid_from,
                "valid_to": request.valid_to,
                "review_status": "proposed_correction",
            }
        )
        return self.repository.propose(claim, request)
