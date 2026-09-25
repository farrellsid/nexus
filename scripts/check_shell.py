"""Checks on the visual shell build (apps/shell) that the ordinary licence gate cannot make.

    python scripts/check_shell.py              # build must already exist in apps/shell/dist
    python scripts/check_shell.py --mode release

It fails when the shell ships anything it should not: more than one Cesium engine, bundled
datasets or models, a hard-coded external host in the page or its styles, a host the smoke test
saw the page contact that is not allowed, or any licence-gate error over the shell's emitted files.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "apps" / "shell"
DATASET_SUFFIXES = (".geojson", ".geojsonl", ".glb", ".gltf", ".mp4", ".webm", ".b3dm", ".pbf")
DATASET_DIRS = ("models", "events", "local_data", "fixtures")
URL = re.compile(r"""(?:https?:)?//([A-Za-z0-9.-]+\.[A-Za-z]{2,})""")
# Text the build copies from libraries, not references the page follows. The scan reads only the
# page and its stylesheets, so these are the few namespace and specification URLs those contain.
NON_REQUEST_HOSTS = {"www.w3.org"}
ANCHOR = re.compile(r"<a\b[^>]*>", re.IGNORECASE)


def dataset_files(files: list[str]) -> list[str]:
    """Bundled data or media: by extension, or by living in a directory upstream used for it."""
    return sorted(
        f
        for f in files
        if f.lower().endswith(DATASET_SUFFIXES) or f.split("/")[0] in DATASET_DIRS
    )


def hard_coded_hosts(texts: dict[str, str]) -> dict[str, set[str]]:
    """Hosts the page or its stylesheets would request, per file.

    Namespace URLs and the targets of plain links (`<a href>`, followed only when a person clicks,
    as the credit to God's Eye View is) are not requests.
    """
    found: dict[str, set[str]] = {}
    for name, text in texts.items():
        text = ANCHOR.sub("", text)
        hosts = {h for h in URL.findall(text) if h not in NON_REQUEST_HOSTS}
        if hosts:
            found[name] = hosts
    return found


def disallowed_hosts(observed: list[str], allowed: list[str]) -> list[str]:
    """Hosts the smoke test saw contacted that are not on the allowed list."""
    return sorted(set(observed) - set(allowed))


def check(mode: str, shell: Path = SHELL) -> list[str]:
    problems: list[str] = []
    dist = shell / "dist"
    if not dist.is_dir():
        return [f"{dist} does not exist: run `npm run build` in apps/shell first"]

    engine = subprocess.run(
        ["node", "scripts/nexus-check-engine.mjs"],
        cwd=shell,
        capture_output=True,
        text=True,
        shell=sys.platform == "win32",
    )
    if engine.returncode != 0:
        problems.append("engine: " + (engine.stdout + engine.stderr).strip().splitlines()[0])

    files = [p.relative_to(dist).as_posix() for p in dist.rglob("*") if p.is_file()]
    for name in dataset_files(files):
        problems.append(f"bundled data or media: {name}")

    page = {"index.html": (dist / "index.html").read_text(encoding="utf-8")}
    for css in (dist / "assets").glob("*.css"):
        page[f"assets/{css.name}"] = css.read_text(encoding="utf-8")
    for name, hosts in hard_coded_hosts(page).items():
        problems.append(f"{name} names external hosts: {sorted(hosts)}")

    observed_path = shell / "test-results" / "smoke-observed.json"
    allowed = json.loads((shell / "tests" / "allowed-hosts.json").read_text(encoding="utf-8"))["hosts"]
    if observed_path.is_file():
        observed = json.loads(observed_path.read_text(encoding="utf-8"))["hosts"]
        for host in disallowed_hosts(observed, allowed):
            problems.append(f"the smoke test saw a request to {host}, which is not allowed")

    gate = subprocess.run(
        [sys.executable, "scripts/check_licences.py", "--mode", mode, "--dist", str(dist)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if gate.returncode != 0:
        errors = [line for line in gate.stdout.splitlines() if line.startswith("ERROR")]
        problems.extend(f"licence gate: {line}" for line in errors or ["failed"])
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=("dev", "release"), default="release")
    problems = check(parser.parse_args().mode)
    for problem in problems:
        print(f"ERROR {problem}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
