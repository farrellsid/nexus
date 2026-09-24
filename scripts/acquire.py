"""Fetch and verify one source on request. This is the only command that touches the network.

    python scripts/acquire.py fetch SOURCE_ID              # dry run: says what it would do
    python scripts/acquire.py fetch SOURCE_ID --confirm    # one fetch, logged
    python scripts/acquire.py baseline SOURCE_ID --attempt ATTEMPT_ID --reviewer NAME --basis TEXT
    python scripts/acquire.py verify SOURCE_ID --confirm   # one fetch, compared with the baseline
    python scripts/acquire.py history SOURCE_ID

Nothing here loops, sleeps or schedules, and nothing runs at startup. Bytes are kept only when the
source's `snapshot_policy` in `licences/source-rights.json` is `store`; the default is `hash_only`.
Run from `backend/` with PYTHONPATH=. like the other scripts.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "licences" / "source-rights.json"
OBJECTS = ROOT / ".local"
KEY_FILE = ROOT / ".local" / "eia-api-key.txt"
EIA_API_HOST = "api.eia.gov"


@dataclass(frozen=True)
class SourceInfo:
    id: str
    url: str
    policy: str
    excerpt: str


def load_source(source_id: str) -> SourceInfo:
    rights = json.loads(RIGHTS.read_text("utf-8"))["sources"]
    for pack in sorted((ROOT / "investigations").glob("*/evidence-pack.json")):
        for source in json.loads(pack.read_text("utf-8"))["sources"]:
            if source["id"] == source_id:
                policy = rights.get(source_id, {}).get("snapshot_policy", "hash_only")
                return SourceInfo(source_id, source["url"], policy, source["excerpt"])
    raise SystemExit(f"Unknown source {source_id}")


def with_credentials(url: str) -> tuple[str, list[str]]:
    """The URL to request and the secrets it carries. Only the EIA API host receives the key."""
    from urllib.parse import urlsplit

    if urlsplit(url).hostname == EIA_API_HOST and "api_key=" not in url:
        key = KEY_FILE.read_text("utf-8").strip()
        return f"{url}{'&' if '?' in url else '?'}api_key={key}", [key]
    return url, []


def _fetch_and_log(source, acquisition, store, transport, resolve):
    """One fetch, one logged attempt; bytes are kept only when the policy says so."""
    from app.acquisition.extraction import extract_json_rows, extract_text
    from app.acquisition.fetch import fetch

    url, secrets = with_credentials(source.url)
    result = fetch(url, transport, resolve)
    leaked = any(secret.encode() in result.body for secret in secrets)
    stored = (
        result.outcome == "ok"
        and not leaked
        and store.put(result.body, source.policy) is not None
    )
    attempt_id = acquisition.log_attempt(source.id, result, stored)
    extraction = None
    kind = (result.content_type or "").lower()
    if result.outcome == "ok" and ("html" in kind or "json" in kind):
        text = result.body.decode("utf-8", "replace")
        extraction = extract_json_rows(text) if "json" in kind else extract_text(text)
        acquisition.record_extraction(result.sha256, extraction)
    return attempt_id, result, extraction


def do_fetch(source, confirm, acquisition, store, transport, resolve):
    print(f"{source.id}: {source.url}")
    print(f"snapshot policy: {source.policy} (bytes are kept only for 'store')")
    if not confirm:
        print(
            "dry run: nothing fetched and nothing written; add --confirm to fetch once"
        )
        return None
    attempt_id, result, extraction = _fetch_and_log(
        source, acquisition, store, transport, resolve
    )
    print(
        f"attempt {attempt_id}: {result.outcome}"
        + (f" ({result.error})" if result.error else "")
    )
    if result.outcome == "ok":
        print(
            f"sha256 {result.sha256}, {result.byte_count} bytes, {result.content_type}"
        )
        print(
            "text sha256",
            extraction.text_sha256 if extraction else "(not HTML; no extraction)",
        )
    return attempt_id


def do_baseline(source_id, attempt_id, reviewer, basis, acquisition):
    from uuid import UUID

    attempt = next(
        (a for a in acquisition.attempts(source_id) if a.id == UUID(str(attempt_id))),
        None,
    )
    if attempt is None or attempt.sha256 is None:
        raise SystemExit(
            "That attempt does not exist for this source or produced no content"
        )
    current = acquisition.current_baseline(source_id)
    identity = acquisition.set_baseline(
        source_id,
        attempt.sha256,
        acquisition.extraction_text_hash(attempt.sha256),
        basis,
        reviewer,
        supersedes=current.id if current else None,
    )
    print(f"baseline {identity} for {source_id}: {attempt.sha256} ({basis})")
    return identity


def do_verify(source, confirm, acquisition, store, transport, resolve):
    from app.acquisition.verification import Attempt, Baseline, verify

    current = acquisition.current_baseline(source.id)
    print(f"{source.id}: {source.url}")
    print("baseline:", f"{current.sha256} ({current.basis})" if current else "none")
    if not confirm:
        print(
            "dry run: nothing fetched and nothing written; add --confirm to verify once"
        )
        return None
    attempt_id, result, extraction = _fetch_and_log(
        source, acquisition, store, transport, resolve
    )
    baseline = (
        Baseline(
            sha256=current.sha256, text_sha256=current.text_sha256, basis=current.basis
        )
        if current
        else None
    )
    verdict = verify(
        baseline,
        Attempt(
            outcome=result.outcome,
            sha256=result.sha256,
            extraction=extraction,
            media_type=result.content_type,
        ),
        [source.excerpt] if source.excerpt else [],
    )
    acquisition.record_verification(
        source.id, attempt_id, current.id if current else None, verdict
    )
    print(
        f"{verdict.state}: {verdict.reason} (comparison {verdict.comparison_readiness})"
    )
    for passage in verdict.passages:
        print(
            f"  passage {'found' if passage.found else 'NOT found'}: {passage.phrase[:90]}"
        )
    return verdict


def _history(source_id, acquisition):
    for attempt in acquisition.attempts(source_id):
        print(
            f"{attempt.started_at:%Y-%m-%d %H:%M} attempt {attempt.id} {attempt.outcome}"
            f" stored={attempt.stored} {attempt.sha256 or ''}"
        )
    for row in acquisition.verifications(source_id):
        print(
            f"verification {row.id} {row.state}: {row.reason} ({row.comparison_readiness})"
        )


def main(argv=None, transport=None, resolve=None, database=None) -> int:
    from app.acquisition.fetch import default_resolver, default_transport
    from app.acquisition.snapshots import ObjectStore
    from app.storage.acquisition import PostgresAcquisition
    from app.storage.database import Database, configured_url

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "verify"):
        command = commands.add_parser(name)
        command.add_argument("source_id")
        command.add_argument("--confirm", action="store_true")
    baseline = commands.add_parser("baseline")
    baseline.add_argument("source_id")
    baseline.add_argument("--attempt", required=True)
    baseline.add_argument("--reviewer", required=True)
    baseline.add_argument("--basis", required=True)
    commands.add_parser("history").add_argument("source_id")
    args = parser.parse_args(argv)

    if database is None:
        url = configured_url()
        if not url:
            raise SystemExit("A local Nexus database is required to log acquisition")
        database = Database(url)
    acquisition = PostgresAcquisition(database)
    store = ObjectStore(OBJECTS)
    transport = transport or default_transport
    resolve = resolve or default_resolver
    if args.command == "fetch":
        do_fetch(
            load_source(args.source_id),
            args.confirm,
            acquisition,
            store,
            transport,
            resolve,
        )
    elif args.command == "verify":
        do_verify(
            load_source(args.source_id),
            args.confirm,
            acquisition,
            store,
            transport,
            resolve,
        )
    elif args.command == "baseline":
        do_baseline(
            args.source_id, args.attempt, args.reviewer, args.basis, acquisition
        )
    else:
        _history(args.source_id, acquisition)
    return 0


if __name__ == "__main__":
    sys.exit(main())
