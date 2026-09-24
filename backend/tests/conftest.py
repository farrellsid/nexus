"""Fixtures shared by the normalisation tests; every database test gets a disposable schema."""

from pathlib import Path
from uuid import uuid4

import pytest
from psycopg import sql

from app.investigation import load_investigations
from app.main import INVESTIGATIONS
from app.normalisation.release import Release
from app.normalisation.vocabulary import load_vocabulary
from app.storage.database import Database, configured_url
from app.storage.normalisation import PostgresNormalisation
from app.storage.reviews import PostgresReviews

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def database():
    url = configured_url()
    if not url:
        pytest.skip("Set NEXUS_DATABASE_URL or run scripts/setup-postgres.py")
    db = Database(url, "test_" + uuid4().hex)
    db.migrate()
    reviews = PostgresReviews(db)
    for investigation in load_investigations(INVESTIGATIONS):
        reviews.initialize(investigation)
    try:
        yield db
    finally:
        with db.connect() as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(db.schema)))


@pytest.fixture
def store(database) -> PostgresNormalisation:
    return PostgresNormalisation(database)


@pytest.fixture(scope="module")
def release() -> Release:
    return Release.model_validate_json(
        (ROOT / "normalisation/releases/2026-09-24.json").read_text("utf-8")
    )


@pytest.fixture(scope="module")
def vocabulary():
    return load_vocabulary(ROOT / "normalisation/vocabulary-v1.json")
