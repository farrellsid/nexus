# How Nexus works: methodology and pipeline

Orientation document for contributors and for future working sessions. It says what is **implemented**, what is **decided** by the user, and what is only **proposed**, and it gives the date each factual claim was checked. Start here, then follow the links. Last verified: 2026-09-23.

## 1. Purpose

Nexus helps a newcomer understand an industrial system (oil, copper, later others) at the level of countries, sectors, major companies, material flows and important infrastructure, using sourced evidence. Detail follows explanatory significance; it does not aim at exhaustive supplier tracking, price prediction or live monitoring. See `README.md` and `docs/design.md`.

## 2. Epistemic principles

These come from `AGENTS.md` and `docs/design.md` and are the reason the pipeline is built the way it is.

- Observations, reported claims, inference and attributed scenarios stay distinct. A forecast is never relabelled as an observation.
- Provenance and temporal versions are preserved: publication date, source-as-of date, event date and record date are separate.
- Nothing is invented. A missing location, date or figure stays visibly missing. "Unknown" is a valid answer.
- A citation does not prove a claim; the passage must support the claim for that material, place and date.
- Shared-origin releases are not independent corroboration.
- The renderer can never alter accepted facts.

### How each principle is represented today (checked 2026-09-23)

| Principle | Representation | Weakness |
|---|---|---|
| Observation vs reported vs forecast | Free-text `claim.kind` (19 distinct values across 44 claims, such as `estimated_flow`, `reported_structure`, `forecast_context`) and metric point `status` (`reported`, `estimate`, `forecast`) | `kind` mixes epistemic status with content type in one string, so it cannot be filtered reliably |
| Claim relationship | Free-text `claim.predicate` | 32 distinct values across 44 claims. Only `produces` appears in both packs, and copper alone uses `produce`, `produced` and `produces`. There is no controlled vocabulary, which blocks cross-industry reasoning |
| Source quality | `Source.review_status` such as `government_analysis_read_via_web` | Combines the class of source with how it was accessed, and is typed by hand rather than recorded by a pipeline |
| Review | `claim.review_status`, plus PostgreSQL proposals, decisions and accepted versions | Every imported claim is `manually_source_checked_candidate`; local review is an editorial decision, not independent verification |
| Unknown | `null` validity bounds, `location_precision` (`unresolved_*`), event precision `not_reported` | Shown inconsistently in the UI; see the warning vocabulary in `docs/frontend-rebuild.md` |
| Ground truth | `claim.ground_truth` is `false` on all 44 claims | By design: no record claims to be established truth |

## 3. Data model (implemented)

- **Source**: title, publisher, url, locator, short excerpt, format, origin group, `checked_on`, rights, independence note.
- **Entity**: id, name, type, coordinates, `location_note`, `location_precision`.
- **Claim**: subject, predicate, object, evidence source ids, kind, source-as-of, valid time, recorded date, statement, caveat, review status.
- **Event**: dated development with precision (`day`, `month`, `quarter`, `not_reported`) and source ids.
- **Metric group**: unit, points (period, value, status), caveat, source ids. Metrics carry no entity link yet.
- **Geography**: sourced point stops and illustrative route lines with precision, role, caveat, source and check date. It is a read-only contract kept outside the review database.
- **Acceptance case**: an authored question with an expected answer and supporting claim ids. Status: authored, **not executed**.
- **Review layer** (`backend/README.md`): proposals, decisions and accepted versions are append-only through database triggers; stale or conflicting reviews return a conflict instead of overwriting.

## 4. The pipeline as it actually is

1. An agent researches with web search and fetch tools, and writes a JSON evidence pack.
2. Pydantic validates the shape, source references and, for published briefs, that no entity is isolated.
3. `scripts/generate-additive-migration.py` compares the pack with the retained database seed, refuses edits or removals, and emits a reviewable SQL migration for additions.
4. The pack is imported as candidate claims and reviewed by hand.

**Not automated:** retrieval, snapshotting, excerpt verification, freshness checks, refresh. On 2026-09-23 only 7 of 17 fetchable HTML excerpts in the oil pack matched their cited pages verbatim; the findings and their causes are in `docs/data-acquisition.md`.

## 5. Analysis rules currently in force

These appear as caveats in the oil and copper packs and are part of the method.

- Aggregate chokepoint flows do not trace cargoes, and overlapping route totals must not be summed.
- Estimates, reported values and forecasts stay labelled; period lengths and definitions are not silently mixed.
- Tonnes are not converted to barrels without a stated basis.
- Capacity is not throughput. A named pipeline's capacity says nothing about actual flow.
- A map point is a label anchor, not a route, boundary or cargo position. A drawn corridor is illustrative and says what it approximates.
- A forecast's attribution is not a measured share.
- A question the evidence cannot support is answered "unknown".

## 6. Process lessons from building this

- Passing tests do not prove a correct render. The Cape of Good Hope line passed every automated check while visibly crossing Africa; only looking at it and sampling points against a land polygon showed it.
- Agent-reported verification must be checked independently. Excerpts reported as verbatim were not all verbatim.
- When a bug is unexplained, bisect from a known-good baseline. Running the same probe inside the working project found a duplicate dependency that hours of option-tweaking had not.
- Parallel agents may work on disjoint files. Shared documents are edited only by the coordinator.
- Coordinates come from a fetched, cited source. A waypoint invented to make a line look right breaks the rule that nothing is invented.

## 7. Decided and proposed work

| Document | Status | Content |
|---|---|---|
| `docs/decisions.md` | Record of user decisions | What is decided, by date; start here for status |
| `docs/recommendations/` | Recommendations from the technical design review; direction approved in `docs/decisions.md` | Ten workstreams, summary in `00-summary.md` |
| `docs/design.md` | Decided direction, partly superseded by later sections | Product scope and milestones |
| `docs/technical-stack.md` | Baseline accepted; some rows now outdated | Stack, storage, retrieval note (2026-09-23) |
| `docs/frontend-rebuild.md` | Rebuild decided by the user; phases proposed; UI in discussion | Data model changes, taxonomy, action layer, warning vocabulary |
| `docs/data-acquisition.md` | Proposal | Acquire, extract, review and refresh pipeline; excerpt check results |
| `docs/data-packs.md` | Idea by the user; mechanics proposed | Installable industry packs, licensing, pack security |
| `docs/ui-flows.md` | First-pass proposal for critique | Shell layout, screens, flows, action verbs, degradation |
| `docs/briefs/technical-design-review-brief.md` | Brief for a separate agent | Ten open technical questions; output goes to `docs/recommendations/` |
| `docs/gods-eye-integration.md` | Superseded in part by the rebuild | Licence boundary and first narrow integration |
| `docs/development-log.md` / `docs/development-status.md` | Record | Checkpoints and current state |

## 8. Known open methodology gaps (checked 2026-09-23)

- No controlled predicate vocabulary, and `claim.kind` mixes two dimensions.
- No representation of conflicting claims for the same subject and predicate.
- No as-of replay; temporal versions are stored but not queryable by date.
- No unit-conversion facts; conversions such as barrels per tonne depend on crude grade and would themselves need sources.
- No freshness thresholds per metric cadence.
- Acceptance cases exist but have never been run.
- Reviewer attribution is self-reported; there is no authentication.
- **Corrections cannot change a claim's relation.** `ReviewService.propose` (`backend/app/review.py`) updates only statement, caveat, evidence ids and validity dates; predicate, kind, subject, object and source-as-of are fixed. A vocabulary migration therefore needs its own mechanism, not review corrections.
- **"Append-only" applies to proposals, decisions and accepted versions, not to the retained seed.** Migrations 002 to 006 disable the `seed_immutable` trigger to replace the seed.
- **Silent id collisions.** The additive generator uses `ON CONFLICT (id) DO NOTHING`, so an incoming record with an existing id but different content is skipped without error.
- **Claim support and coverage labels.** O-C26 is not supported by its retained excerpt, and the oil pack's "developments through 2026-09-10" label is contradicted by later evidence (details in `docs/data-acquisition.md`).
- Ten workstream recommendations on these gaps are in `docs/recommendations/00-summary.md`. They are recommendations, not decisions.

## 9. Keeping this current

When a decision changes, update the relevant record and add a dated entry to `docs/development-log.md`. Mark each decision as the user's or the assistant's proposal, and give the date a factual claim was verified.
