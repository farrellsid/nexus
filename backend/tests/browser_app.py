"""Disposable browser-test database. Never serves the user's review schema."""

import os
from contextlib import asynccontextmanager
from uuid import uuid4

from psycopg import sql

from app.investigation import load_investigations
from app.main import INVESTIGATIONS, create_app
from app.storage.database import Database, configured_url
from app.storage.reviews import PostgresReviews

data = load_investigations(INVESTIGATIONS)
url = configured_url()
database = Database(url, "browser_test_" + uuid4().hex) if url else None
if os.environ.get("NEXUS_REQUIRE_DATABASE_TESTS") == "1" and database is None:
    raise RuntimeError("Browser database tests require PostgreSQL")

repository = PostgresReviews(database) if database else None
app = create_app(data, repository, review_origins={"http://127.0.0.1:5174"})


@asynccontextmanager
async def lifespan(application):
    if database:
        database.migrate()
        for investigation in data:
            repository.initialize(investigation)
    try:
        yield
    finally:
        if database:
            with database.connect() as connection:
                connection.execute(
                    sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(database.schema))
                )


app.router.lifespan_context = lifespan
