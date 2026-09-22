"""Initialize/start a private project-local PostgreSQL cluster, without a Windows service."""

import json
import secrets
import subprocess
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
BIN = LOCAL / "postgres-runtime/pgsql/bin"
DATA = LOCAL / "postgres-data"
CONFIG = LOCAL / "database.json"


def run(program, *args, check=True):
    return subprocess.run(
        [str(BIN / f"{program}.exe"), *map(str, args)],
        check=check,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def main():
    if not (BIN / "pg_ctl.exe").exists():
        raise SystemExit(
            "First unpack the PostgreSQL Windows archive into .local/postgres-runtime."
        )
    LOCAL.mkdir(exist_ok=True)
    if not (DATA / "PG_VERSION").exists():
        password = secrets.token_hex(24)
        password_file = LOCAL / "initdb-password"
        password_file.write_text(password, encoding="utf-8")
        try:
            run(
                "initdb",
                "-D",
                DATA,
                "-U",
                "nexus",
                "--auth=scram-sha-256",
                "--pwfile",
                password_file,
                "--encoding=UTF8",
                "--locale=C",
            )
        finally:
            password_file.unlink(missing_ok=True)
        CONFIG.write_text(
            json.dumps(
                {
                    "url": f"postgresql://nexus:{password}@127.0.0.1:55432/nexus",
                }
            ),
            encoding="utf-8",
        )
    if not CONFIG.exists():
        raise SystemExit(
            "Cluster exists but database.json is missing. Restore its connection configuration."
        )
    url = json.loads(CONFIG.read_text("utf-8"))["url"]
    try:
        with psycopg.connect(url, connect_timeout=2):
            database_is_running = True
    except psycopg.OperationalError:
        database_is_running = False
    if not database_is_running:
        run(
            "pg_ctl",
            "-D",
            DATA,
            "-l",
            LOCAL / "postgres.log",
            "-o",
            "-h 127.0.0.1 -p 55432",
            "-w",
            "start",
        )
    with psycopg.connect(
        url.rsplit("/", 1)[0] + "/postgres", autocommit=True
    ) as connection:
        if not connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'nexus'"
        ).fetchone():
            connection.execute("CREATE DATABASE nexus")
    print(
        "Nexus PostgreSQL is ready on 127.0.0.1:55432. Credentials stay in .local/database.json."
    )


if __name__ == "__main__":
    main()
