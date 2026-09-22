"""Native PostgreSQL backups; credentials go through the process environment, not argv."""

import os
import subprocess
from pathlib import Path

from psycopg.conninfo import conninfo_to_dict

from app.storage.database import ROOT, Database


def postgres_tool(database: Database, tool: str, arguments: list[str]) -> None:
    default = ROOT / ".local/postgres-runtime/pgsql/bin"
    directory = Path(os.environ.get("NEXUS_PG_BIN", str(default)))
    executable = directory / (tool + (".exe" if os.name == "nt" else ""))
    if not executable.exists():
        raise RuntimeError("Set NEXUS_PG_BIN to your PostgreSQL bin directory")
    settings = conninfo_to_dict(database.url)
    environment = os.environ.copy()
    for key, name in {
        "host": "PGHOST",
        "port": "PGPORT",
        "user": "PGUSER",
        "password": "PGPASSWORD",
        "dbname": "PGDATABASE",
        "sslmode": "PGSSLMODE",
    }.items():
        if key in settings:
            environment[name] = settings[key]
    result = subprocess.run(
        [str(executable), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if result.returncode:
        # Do not include connection settings or arbitrary stderr in user-facing errors.
        raise RuntimeError(f"{tool} failed with exit code {result.returncode}")


def create_backup(database: Database, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite a previous backup, even if a filename is accidentally reused.
    with target.open("xb"):
        pass
    try:
        postgres_tool(
            database,
            "pg_dump",
            ["--format=custom", "--no-owner", "--schema", database.schema, "--file", str(target)],
        )
    except Exception:
        target.unlink(missing_ok=True)
        raise


def restore_backup(database: Database, archive: Path) -> None:
    """Restore into an empty database/schema. Never issue --clean or drop existing data."""
    with database.connect() as connection:
        if connection.execute(
            "SELECT 1 FROM pg_namespace WHERE nspname = %s", (database.schema,)
        ).fetchone():
            raise ValueError("Restore requires a database without the target schema")
    postgres_tool(
        database,
        "pg_restore",
        [
            "--no-owner",
            "--exit-on-error",
            "--single-transaction",
            "--dbname",
            conninfo_to_dict(database.url)["dbname"],
            str(archive),
        ],
    )
