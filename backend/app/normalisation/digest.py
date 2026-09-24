"""Stable content hashing for release documents (same algorithm as review history hashes)."""

import hashlib
import json


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
