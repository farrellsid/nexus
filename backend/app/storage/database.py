"""Connection configuration and transactional, checksummed SQL migrations."""

import hashlib
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[3]

# Migration 004 originally assumed the oil seed already existed. Its guarded
# replacement has identical effects for upgraded databases and safely becomes a
# no-op on fresh databases, where fixture initialization imports the full pack.
COMPATIBLE_MIGRATION_CHECKSUMS = {
    "004_expand_oil_routes.sql": {
        "65a67a3004d2e953d68b0bde97f1b9eed9d9aa5d30ede44c73098a8d8e9b5e09"
    }
}


def configured_url() -> str | None:
    if "NEXUS_DATABASE_URL" in os.environ:
        return os.environ["NEXUS_DATABASE_URL"] or None
    config = ROOT / ".local/database.json"
    if config.exists():
        return json.loads(config.read_text("utf-8"))["url"]
    return None


class Database:
    def __init__(self, url: str, schema: str = "nexus"):
        if not schema.replace("_", "").isalnum():
            raise ValueError("Invalid database schema name")
        self.url = url
        self.schema = schema

    def connect(self):
        return psycopg.connect(
            self.url,
            row_factory=dict_row,
            connect_timeout=5,
            options=f"-c search_path={self.schema},pg_catalog -c statement_timeout=10000",
        )

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (self.schema,))
            connection.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema))
            )
            connection.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    name text PRIMARY KEY, sha256 text NOT NULL,
                    applied_at timestamptz NOT NULL DEFAULT clock_timestamp()
                )
            """)
            for path in sorted((Path(__file__).parent / "migrations").glob("*.sql")):
                source = path.read_text("utf-8")
                checksum = hashlib.sha256(source.encode()).hexdigest()
                existing = connection.execute(
                    "SELECT sha256 FROM schema_migrations WHERE name = %s", (path.name,)
                ).fetchone()
                if existing:
                    if existing["sha256"] != checksum:
                        compatible = COMPATIBLE_MIGRATION_CHECKSUMS.get(path.name, set())
                        if existing["sha256"] not in compatible:
                            raise RuntimeError(f"Applied migration changed: {path.name}")
                        connection.execute(
                            "UPDATE schema_migrations SET sha256 = %s WHERE name = %s",
                            (checksum, path.name),
                        )
                    continue
                connection.execute(source)
                connection.execute(
                    "INSERT INTO schema_migrations(name, sha256) VALUES (%s, %s)",
                    (path.name, checksum),
                )
