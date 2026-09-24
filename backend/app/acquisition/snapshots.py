"""A write-once, content-addressed store for fetched bytes.

Bytes are kept only when the source's snapshot policy is `store`. A path is named by the SHA-256
of its content, so an identical put is a no-op and a mismatching file is an integrity failure,
never a silent overwrite.
"""

import hashlib
import os
import tempfile
from pathlib import Path

from app.acquisition.policy import SnapshotPolicy, guard_storage
from app.knowledge import Record


class IntegrityError(Exception):
    """A stored object no longer matches its hash."""


class StoredObject(Record):
    sha256: str
    size: int
    path: Path


class ObjectStore:
    def __init__(self, root: Path):
        self.root = root

    def _path(self, sha256: str) -> Path:
        return self.root / "objects" / "sha256" / sha256[:2] / sha256

    def put(self, data: bytes, policy: SnapshotPolicy) -> StoredObject | None:
        """Store the bytes if the policy allows; return None (and write nothing) otherwise."""
        if not guard_storage(policy):
            return None
        sha256 = hashlib.sha256(data).hexdigest()
        path = self._path(sha256)
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
                raise IntegrityError(f"{path} does not match its hash; not overwriting")
            return StoredObject(sha256=sha256, size=len(data), path=path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".partial-")
        try:
            with os.fdopen(handle, "wb") as file:
                file.write(data)
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
        return StoredObject(sha256=sha256, size=len(data), path=path)

    def get(self, sha256: str) -> bytes | None:
        path = self._path(sha256)
        if not path.exists():
            return None
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha256:
            raise IntegrityError(f"{path} does not match its hash")
        return data
