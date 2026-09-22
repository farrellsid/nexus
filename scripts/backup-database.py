"""Create a timestamped backup of Nexus's retained evidence and review history."""

from datetime import UTC, datetime
from uuid import uuid4

from app.storage.backup import create_backup
from app.storage.database import ROOT, Database, configured_url

url = configured_url()
if not url:
    raise SystemExit("Configure PostgreSQL before creating a database backup")
target = (
    ROOT
    / ".local/backups"
    / f"nexus-{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid4().hex[:6]}.dump"
)
create_backup(Database(url), target)
print(f"Backup saved: {target}")
