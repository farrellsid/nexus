"""Propose evidence corrections for a person to review; never edit recorded history.

A repair mapping (see `investigations/*/repairs/`) says which claims should cite which
replacement or additional sources. Each becomes an ordinary correction proposal through the
review service, so nothing changes until someone accepts it. Run with `--dry-run` first.

    python scripts/propose_evidence_repairs.py investigations/02-oil-system/repairs/X.json --dry-run
    python scripts/propose_evidence_repairs.py investigations/02-oil-system/repairs/X.json
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

AUTHOR = "Nexus evidence repair (prepared by the assistant, awaiting human review)"


@dataclass(frozen=True)
class Correction:
    claim_id: str
    before: list[str]
    after: list[str]
    why: str


def plan_corrections(
    claims: dict[str, list[str]], corrections: list[dict], known_sources: set[str]
) -> list[Correction]:
    """Validate a mapping against the real claims and sources and return the changes."""
    planned: list[Correction] = []
    seen: set[str] = set()
    for item in corrections:
        claim_id = item["claim_id"]
        if claim_id not in claims:
            raise ValueError(f"unknown claim {claim_id}")
        if claim_id in seen:
            raise ValueError(f"claim {claim_id} appears more than once")
        seen.add(claim_id)
        why = (item.get("why") or "").strip()
        if not why:
            raise ValueError(f"{claim_id}: a reason is required")
        before = list(claims[claim_id])
        after = list(before)
        for old, new in item.get("replace", {}).items():
            if old not in after:
                raise ValueError(f"{claim_id} does not cite {old}")
            after[after.index(old)] = new
        for new in item.get("add", []):
            if new not in after:
                after.append(new)
        unknown = [source for source in after if source not in known_sources]
        if unknown:
            raise ValueError(f"{claim_id}: unknown source {unknown[0]}")
        if after == before:
            raise ValueError(f"{claim_id}: correction changes nothing")
        if len(set(after)) != len(after):
            raise ValueError(f"{claim_id}: the result cites a source twice")
        planned.append(Correction(claim_id, before, after, why))
    return planned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mapping", type=Path)
    parser.add_argument(
        "--dry-run", action="store_true", help="print the plan and write nothing"
    )
    args = parser.parse_args()

    from app.investigation import load_investigations
    from app.main import INVESTIGATIONS
    from app.review import ProposalRequest, ReviewService
    from app.storage.database import Database, configured_url
    from app.storage.reviews import PostgresReviews

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    investigation = next(
        item
        for item in load_investigations(INVESTIGATIONS)
        if item.pack.case_id == mapping["case_id"]
    )
    claims = {claim.id: claim for claim in investigation.pack.claims}
    known = {source.id for source in investigation.pack.sources}
    plan = plan_corrections(
        {cid: claim.evidence_ids for cid, claim in claims.items()},
        mapping["corrections"],
        known,
    )

    for item in plan:
        print(
            f"{item.claim_id:6} {', '.join(item.before)}  ->  {', '.join(item.after)}"
        )
    print(f"\n{len(plan)} correction proposal(s) planned for {mapping['case_id']}")
    if args.dry_run:
        return 0

    url = configured_url()
    if not url:
        raise SystemExit("A local Nexus database is required to record proposals")
    repository = PostgresReviews(Database(url))
    service = ReviewService(investigation.pack, repository)
    for item in plan:
        claim = claims[item.claim_id]
        history = repository.history(item.claim_id)
        request = ProposalRequest(
            request_id=uuid5(
                NAMESPACE_URL, f"nexus:repair:{mapping['id']}:{item.claim_id}"
            ),
            base_revision=history.current_revision,
            statement=claim.statement,
            caveat=claim.caveat,
            evidence_ids=item.after,
            valid_from=claim.valid_from,
            valid_to=claim.valid_to,
            author=AUTHOR,
            reason=item.why,
        )
        service.propose(item.claim_id, request)
    print("recorded; the proposals are pending in the review panel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
