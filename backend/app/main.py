"""Composition root for the fixture reader and optional PostgreSQL review workbench."""

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from psycopg import OperationalError
from psycopg.errors import UniqueViolation
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.investigation import Investigation, load_investigations
from app.knowledge import Neighborhood, neighborhood
from app.normalisation.release import EntityRecord, MeasurementRecord
from app.review import (
    DecisionRequest,
    ProposalRequest,
    ReviewAvailability,
    ReviewConflict,
    ReviewHistory,
    ReviewService,
)
from app.storage.database import Database, configured_url
from app.storage.normalisation import ClaimProjection, PostgresNormalisation
from app.storage.reviews import PostgresReviews

INVESTIGATIONS = Path(__file__).resolve().parents[2] / "investigations"
PILOT = INVESTIGATIONS / "01-kamoa-to-cables"
DEFAULT_CASE = "kamoa-to-cables"


def create_app(
    investigation: Investigation | list[Investigation] | None = None,
    repository: PostgresReviews | None = None,
    review_origins: set[str] | None = None,
    normalisation: PostgresNormalisation | None = None,
) -> FastAPI:
    if investigation is None:
        loaded = load_investigations(INVESTIGATIONS)
    elif isinstance(investigation, list):
        loaded = investigation
    else:
        loaded = [investigation]
    investigations = {item.pack.case_id: item for item in loaded}
    default_case = DEFAULT_CASE if DEFAULT_CASE in investigations else next(iter(investigations))

    @asynccontextmanager
    async def lifespan(application):
        if (
            application.state.reviews is None
            and investigation is None
            and (url := configured_url())
        ):
            database = Database(url)
            database.migrate()
            storage = PostgresReviews(database)
            for item in investigations.values():
                storage.initialize(item)
            application.state.reviews = storage
            application.state.normalisation = PostgresNormalisation(database)
        yield

    app = FastAPI(title="Nexus evidence workbench", version="0.2.0", lifespan=lifespan)
    app.state.reviews = repository
    app.state.normalisation = normalisation
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @app.middleware("http")
    async def protect_local_writes(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            allowed = (
                review_origins
                if review_origins is not None
                else {"http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000"}
            )
            if request.headers.get("x-nexus-review") != "1" or (origin and origin not in allowed):
                return JSONResponse(
                    status_code=403, content={"detail": "Local review request required"}
                )
        return await call_next(request)

    @app.exception_handler(ReviewConflict)
    async def conflict_handler(request, error):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(UniqueViolation)
    async def duplicate_handler(request, error):
        return JSONResponse(
            status_code=409, content={"detail": "Request identity conflict. Reload history."}
        )

    @app.exception_handler(OperationalError)
    async def database_unavailable(request, error):
        return JSONResponse(
            status_code=503,
            content={"detail": "Database unavailable. Reload history before retrying any changes."},
        )

    def reviews() -> PostgresReviews:
        if app.state.reviews is None:
            raise HTTPException(
                status_code=503, detail="PostgreSQL review storage is not configured"
            )
        return app.state.reviews

    def normalised() -> PostgresNormalisation:
        if app.state.normalisation is None:
            raise HTTPException(
                status_code=503, detail="PostgreSQL normalisation storage is not configured"
            )
        return app.state.normalisation

    def current_investigation(case_id: str) -> Investigation:
        if case_id not in investigations:
            raise HTTPException(status_code=404, detail="Investigation not found")
        data = investigations[case_id]
        if app.state.reviews is None:
            return data
        claim_ids = [claim.id for claim in data.pack.claims]
        current = {claim.id: claim for claim in reviews().current_claims(claim_ids)}
        pack = data.pack.model_copy(
            update={"claims": [current[claim.id] for claim in data.pack.claims]}
        )
        return data.model_copy(update={"pack": pack})

    @app.get("/api/investigation", response_model=Investigation)
    def get_investigation(case_id: str = default_case) -> Investigation:
        return current_investigation(case_id)

    @app.get("/api/investigations")
    def list_investigations() -> list[dict[str, str]]:
        return [
            {
                "case_id": item.pack.case_id,
                "title": item.pack.briefing.title if item.pack.briefing else item.pack.case_id,
                "scope": item.pack.scope,
            }
            for item in investigations.values()
        ]

    @app.get("/api/entities/{entity_id}/neighborhood", response_model=Neighborhood)
    def get_neighborhood(
        entity_id: str,
        depth: int = Query(1, ge=1, le=2),
        case_id: str = default_case,
    ) -> Neighborhood:
        try:
            return neighborhood(current_investigation(case_id).pack, entity_id, depth)
        except KeyError:
            raise HTTPException(status_code=404, detail="Entity not found") from None

    @app.get("/api/review/status", response_model=ReviewAvailability)
    def review_status() -> ReviewAvailability:
        enabled = app.state.reviews is not None
        return ReviewAvailability(
            enabled=enabled, mode="postgresql" if enabled else "read_only_fixture"
        )

    @app.get("/api/normalisation/status")
    def normalisation_status() -> dict[str, str | None]:
        return {"accepted_release_id": normalised().accepted_release_id()}

    @app.get("/api/claims/{claim_id}/projection", response_model=ClaimProjection | None)
    def claim_projection(claim_id: str) -> ClaimProjection | None:
        if not any(claim_id in {claim.id for claim in item.pack.claims} for item in loaded):
            raise HTTPException(status_code=404, detail="Claim not found")
        return normalised().claim_projection(claim_id)

    @app.get("/api/entities/resolve", response_model=EntityRecord | None)
    def resolve_entity(case_id: str, legacy_id: str) -> EntityRecord | None:
        if case_id not in investigations:
            raise HTTPException(status_code=404, detail="Investigation not found")
        return normalised().resolve_alias(case_id, legacy_id)

    @app.get("/api/measurements", response_model=list[MeasurementRecord])
    def measurements(entity: str | None = None) -> list[MeasurementRecord]:
        return normalised().measurements(entity)

    @app.get("/api/claims/{claim_id}/history", response_model=ReviewHistory)
    def history(claim_id: str) -> ReviewHistory:
        try:
            return reviews().history(claim_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Claim not found") from None

    @app.post("/api/claims/{claim_id}/proposals", response_model=ReviewHistory)
    def propose(claim_id: str, request: ProposalRequest) -> ReviewHistory:
        try:
            owner = next(
                (
                    item
                    for item in investigations.values()
                    if claim_id in {claim.id for claim in item.pack.claims}
                ),
                None,
            )
            if owner is None:
                raise KeyError(claim_id)
            return ReviewService(owner.pack, reviews()).propose(claim_id, request)
        except KeyError:
            raise HTTPException(status_code=404, detail="Claim not found") from None
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None

    @app.post("/api/proposals/{proposal_id}/decision", response_model=ReviewHistory)
    def decide(proposal_id: UUID, request: DecisionRequest) -> ReviewHistory:
        try:
            return reviews().decide(proposal_id, request)
        except KeyError:
            raise HTTPException(status_code=404, detail="Proposal not found") from None

    return app


app = create_app()
