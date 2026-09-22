"""Restore a Nexus archive into a new database; leave the active database unchanged."""

import argparse
from pathlib import Path

import psycopg
from app.storage.backup import restore_backup
from app.storage.database import Database, configured_url
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

parser = argparse.ArgumentParser()
parser.add_argument("archive", type=Path)
parser.add_argument(
    "--database",
    required=True,
    help="A new database name; existing databases are refused",
)
args = parser.parse_args()
url = configured_url()
if not url:
    raise SystemExit("Configure PostgreSQL first")
settings = conninfo_to_dict(url)
with psycopg.connect(url, autocommit=True) as connection:
    connection.execute(
        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(args.database))
    )
restored = Database(make_conninfo(**{**settings, "dbname": args.database}))
restore_backup(restored, args.archive)
print(f"Restored into {args.database}. The active Nexus database has not been changed.")
