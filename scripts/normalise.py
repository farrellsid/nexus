"""Check, record and decide on a normalisation release. Recording alone changes no claim.

    python scripts/normalise.py check                     # no database needed
    python scripts/normalise.py record --dry-run
    python scripts/normalise.py record
    python scripts/normalise.py decide nx-norm-2026-09-24 accept --reviewer NAME --reason TEXT

`record` stores the release for review; nothing reads it until a person records an accept
decision. Back up the database before the first `record`.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "normalisation" / "releases"


def latest_release() -> Path:
    """The newest release file: by date, then by revision (`-r2` follows the bare date)."""

    def order(path: Path):
        match = re.match(r"(\d{4}-\d{2}-\d{2})(?:-r(\d+))?$", path.stem)
        return (match.group(1), int(match.group(2) or 1)) if match else ("", 0)

    return max(RELEASES.glob("*.json"), key=order)


DEFAULT_RELEASE = latest_release()
VOCABULARY = ROOT / "normalisation" / "vocabulary-v1.json"


def _metric_texts() -> dict[tuple[str, str], list[str]]:
    from app.normalisation.measurements import read_metric_points

    texts: dict[tuple[str, str], list[str]] = {}
    for directory in sorted((ROOT / "investigations").iterdir()):
        pack = directory / "evidence-pack.json"
        if pack.is_file():
            case_id = json.loads(pack.read_text("utf-8"))["case_id"]
            texts |= {
                (case_id, metric): v for metric, v in read_metric_points(pack).items()
            }
    return texts


def check(release_path: Path) -> list[str]:
    """Return every problem found in the release against the real packs and vocabulary."""
    from app.investigation import load_investigations
    from app.normalisation.release import Release, validate_release
    from app.normalisation.vocabulary import load_vocabulary

    release = Release.model_validate_json(release_path.read_text("utf-8"))
    return validate_release(
        release,
        load_vocabulary(VOCABULARY),
        load_investigations(ROOT / "investigations"),
        _metric_texts(),
    )


def _print_check(release_path: Path) -> int:
    problems = check(release_path)
    for problem in problems:
        print(f"PROBLEM  {problem}")
    print(f"{release_path.name}: {len(problems)} problem(s)")
    return 1 if problems else 0


def _record(release_path: Path, dry_run: bool) -> int:
    if _print_check(release_path):
        return 1
    from app.normalisation.release import Release
    from app.normalisation.vocabulary import load_vocabulary
    from app.storage.database import Database, configured_url
    from app.storage.normalisation import PostgresNormalisation

    release = Release.model_validate_json(release_path.read_text("utf-8"))
    print(
        f"release {release.release_id}: {len(release.claims)} claims, {len(release.sources)} "
        f"sources, {len(release.entities)} entities, {len(release.measurements)} measurements"
    )
    if dry_run:
        print("dry run: nothing written")
        return 0
    url = configured_url()
    if not url:
        raise SystemExit("A local Nexus database is required to record a release")
    store = PostgresNormalisation(Database(url))
    print(
        f"recorded {store.record_release(release, load_vocabulary(VOCABULARY))}; pending review"
    )
    return 0


def _decide(release_id: str, decision: str, reviewer: str, reason: str) -> int:
    from app.storage.database import Database, configured_url
    from app.storage.normalisation import PostgresNormalisation

    url = configured_url()
    if not url:
        raise SystemExit("A local Nexus database is required to record a decision")
    PostgresNormalisation(Database(url)).decide(release_id, decision, reviewer, reason)
    print(f"{decision} recorded for {release_id} by {reviewer}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "record"):
        command = commands.add_parser(name)
        command.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
        if name == "record":
            command.add_argument("--dry-run", action="store_true")
    decide = commands.add_parser("decide")
    decide.add_argument("release_id")
    decide.add_argument("decision", choices=("accept", "reject"))
    decide.add_argument("--reviewer", required=True)
    decide.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    if args.command == "check":
        return _print_check(args.release)
    if args.command == "record":
        return _record(args.release, args.dry_run)
    return _decide(args.release_id, args.decision, args.reviewer, args.reason)


if __name__ == "__main__":
    sys.exit(main())
