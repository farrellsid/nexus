"""Licence gate: decide what may ship, mechanically, before anything is published.

Two modes. `dev` reports and fails only on structural problems (a source with no rights
entry, a forbidden file in the build). `release` also fails on anything unverified or
missing a licence file. Manifests live in `licences/`; see `docs/decisions.md`.

    python scripts/check_licences.py --mode dev
    python scripts/check_licences.py --mode release --dist apps/web/dist
"""

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICENCE_FILES = ("LICENSE", "LICENSE-CONTENT.md")
PACKS = (
    "investigations/01-kamoa-to-cables/evidence-pack.json",
    "investigations/02-oil-system/evidence-pack.json",
)


@dataclass(frozen=True)
class Finding:
    level: str  # "error" fails the run; "note" is reported only
    code: str
    message: str


def _needs_verification(mode: str) -> str:
    """Unverified material is a note while developing and an error at release."""
    return "error" if mode == "release" else "note"


def evaluate_sources(
    sources: list[dict], rights: dict[str, dict], mode: str
) -> list[Finding]:
    findings: list[Finding] = []
    known = {source["id"] for source in sources}
    for source in sources:
        entry = rights.get(source["id"])
        if entry is None:
            findings.append(
                Finding(
                    "error",
                    "source-missing-rights",
                    f"{source['id']} has no rights entry",
                )
            )
            continue
        status, release = entry["redistribution"], entry["release_excerpt"]
        if status == "blocked" and release == "include":
            findings.append(
                Finding(
                    "error", "source-blocked-included", f"{source['id']} is blocked"
                )
            )
        elif status == "unverified" and release == "include":
            findings.append(
                Finding(
                    _needs_verification(mode),
                    "source-unverified-included",
                    f"{source['id']} ({entry['publisher']}) is unverified but its excerpt is included",
                )
            )
        elif release == "withhold":
            findings.append(
                Finding(
                    "note",
                    "source-withheld",
                    f"{source['id']} excerpt withheld from release",
                )
            )
    for source_id in sorted(set(rights) - known):
        findings.append(
            Finding(
                "error",
                "rights-entry-orphan",
                f"rights entry {source_id} matches no source",
            )
        )
    return findings


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """`*` stays inside one directory; `**` crosses directories."""
    parts = re.split(r"(\*\*|\*)", pattern)
    body = "".join(
        ".*" if part == "**" else "[^/]*" if part == "*" else re.escape(part)
        for part in parts
    )
    return re.compile(f"^{body}$")


def _matches(path: str, patterns: list[str]) -> bool:
    return any(_glob_regex(pattern).match(path) for pattern in patterns)


def evaluate_dist(files: list[str], components: list[dict], mode: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(files):
        forbidden = [
            c for c in components if _matches(path, c.get("forbidden_globs", []))
        ]
        if forbidden:
            findings.append(
                Finding(
                    "error",
                    "emitted-forbidden",
                    f"{path} is forbidden ({forbidden[0]['id']})",
                )
            )
            continue
        owners = [
            c
            for c in components
            if c.get("included") and _matches(path, c.get("emitted_globs", []))
        ]
        if not owners:
            findings.append(
                Finding("error", "emitted-uncovered", f"{path} matches no component")
            )
        elif owners[0]["redistribution"] in (
            "blocked",
            "unverified",
            "local_only",
            "reference_only",
        ):
            level = (
                "error"
                if owners[0]["redistribution"] == "blocked"
                else _needs_verification(mode)
            )
            findings.append(
                Finding(
                    level, "emitted-unverified", f"{path} belongs to {owners[0]['id']}"
                )
            )
    return findings


def judge_licence(expression: str | None, allowed: set[str]) -> str:
    """Return "allowed" if the SPDX-style expression satisfies the allow-list, else "review"."""
    if not expression or not expression.strip():
        return "review"
    text = expression.strip()
    while text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    alternatives = re.split(r"\s+OR\s+", text, flags=re.IGNORECASE)
    for alternative in alternatives:
        required = re.split(r"\s+AND\s+", alternative.strip("() "), flags=re.IGNORECASE)
        if all(item.strip("() ") in allowed for item in required):
            return "allowed"
    return "review"


def evaluate_npm_runtime(
    lock: dict, licence_of: Callable[[str], str | None], allowed: set[str], mode: str
) -> list[Finding]:
    findings: list[Finding] = []
    for key, package in lock.get("packages", {}).items():
        if not key or package.get("dev"):
            continue
        name = key.split("node_modules/")[-1]
        expression = licence_of(key)
        if judge_licence(expression, allowed) == "review":
            findings.append(
                Finding(
                    _needs_verification(mode),
                    "npm-licence-review",
                    f"{name} declares {expression!r}; needs a human decision",
                )
            )
    return findings


def evaluate_licence_files(root: Path, mode: str) -> list[Finding]:
    return [
        Finding(
            _needs_verification(mode), "licence-file-missing", f"{name} does not exist"
        )
        for name in LICENCE_FILES
        if not (root / name).is_file()
    ]


def _npm_licence_reader(web: Path) -> Callable[[str], str | None]:
    """Read a package's declared licence from where the lockfile says it is installed."""

    def read(key: str) -> str | None:
        manifest = web / key / "package.json"
        if not manifest.is_file():
            return None
        data = json.loads(manifest.read_text(encoding="utf-8"))
        value = data.get("license") or data.get("licenses")
        if isinstance(value, dict):
            return value.get("type")
        if isinstance(value, list):
            return " OR ".join(item.get("type", "") for item in value)
        return value

    return read


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(mode: str, dist: Path, root: Path = ROOT) -> list[Finding]:
    policy = _load(root / "licences" / "policy.json")
    allowed = set(policy["allowed_licences"])
    components = _load(root / "licences" / "components.json")["components"]
    source_rights = _load(root / "licences" / "source-rights.json")["sources"]
    sources = [s for pack in PACKS for s in _load(root / pack)["sources"]]

    findings = evaluate_licence_files(root, mode) + evaluate_sources(
        sources, source_rights, mode
    )
    web = root / "apps" / "web"
    lock = web / "package-lock.json"
    if lock.is_file() and (web / "node_modules").is_dir():
        findings += evaluate_npm_runtime(
            _load(lock), _npm_licence_reader(web), allowed, mode
        )
    else:
        findings.append(
            Finding(
                "note", "npm-skipped", "no lockfile or node_modules; npm not checked"
            )
        )
    if dist.is_dir():
        files = [p.relative_to(dist).as_posix() for p in dist.rglob("*") if p.is_file()]
        findings += evaluate_dist(files, components, mode)
    else:
        findings.append(
            Finding(
                "note", "dist-skipped", f"{dist} not built; emitted files not checked"
            )
        )
    for service in (c for c in components if c.get("kind") == "service"):
        if (
            service["redistribution"] != "allowed"
            and service.get("release_use") == "enabled"
        ):
            findings.append(
                Finding(
                    _needs_verification(mode),
                    "service-unverified",
                    f"{service['id']} enabled",
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=("dev", "release"), default="dev")
    parser.add_argument("--dist", type=Path, default=ROOT / "apps" / "web" / "dist")
    args = parser.parse_args()

    findings = run(args.mode, args.dist)
    for finding in findings:
        print(f"{finding.level.upper():5} {finding.code:28} {finding.message}")
    counts = Counter(f.level for f in findings)
    print(f"\nmode={args.mode}: {counts['error']} error(s), {counts['note']} note(s)")
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
