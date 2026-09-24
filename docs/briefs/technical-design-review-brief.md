# Brief: technical design review for Nexus

You are being asked to reason carefully about a set of open technical design questions for Nexus and to write recommendations. This is **analysis and design work only**. Read the repository, inspect the real data, and write findings. Do not change code or existing documents.

Date of writing: 2026-09-23. Repository root: `D:\Projects\Nexus` (Windows; Python venv at `.venv`; frontend in `apps/web`).

## Rules

1. **Write only new files**, under `docs/recommendations/`. Do not edit code, tests, data packs, migrations or existing docs. Do not commit. Do not install packages or start servers. Read-only scripts against the packs and the repo are encouraged.
2. **Ground every recommendation in the actual data and code.** The people asking have surface-level intuitions; your value is knowing the reality. When you cite a fact about the repo, say how you checked it (file path, or the command or script you ran).
3. **External facts must be fetched, not recalled.** Cite the URL you actually retrieved. Mark anything you could not verify as **UNVERIFIED** and say why. This project treats an unverified claim presented as fact as a serious defect. Never invent identifiers, licences, prices or schemas.
4. **Disagree when the evidence says so.** The user's leanings below are inputs to evaluate, not conclusions to confirm. If one is wrong or risky, say so plainly with reasons and offer the better option.
5. **Respect the project's non-negotiables** (section 3), especially append-only review history and "nothing is invented".
6. **Be concrete.** Prefer field names, table shapes, mappings and migration steps over general advice. Prefer short over long.

## 1. Read first, in this order

`AGENTS.md`, `README.md`, `docs/methodology.md`, `docs/frontend-rebuild.md`, `docs/data-acquisition.md`, `docs/data-packs.md`, `docs/technical-stack.md`, `docs/design.md` (the 2026-09-21 section), `docs/development-log.md` (top entries), `backend/README.md`.

Then the code and data: `backend/app/evidence.py`, `knowledge.py`, `review.py`, `investigation.py`, `geography.py`, `backend/app/storage/` (including `migrations/` and `reviews.py`), `scripts/generate-additive-migration.py`, `investigations/01-kamoa-to-cables/` and `investigations/02-oil-system/` (evidence packs, acceptance cases, geography), and `contracts/openapi.json`.

Some documents predate the rebuild decision. Where they conflict, `docs/frontend-rebuild.md` and `docs/methodology.md` are newer. Report contradictions you find.

## 2. Facts already established (re-verify anything you rely on)

Checked by the previous assistant on 2026-09-22 and 2026-09-23:

- The corpus is small: 43 entities, 44 claims and 34 sources across both packs. The oil pack has 26 claims, 23 entities and 11 metric groups; copper has 18 claims.
- `claim.predicate` is free text: 32 distinct values across 44 claims. Only `produces` appears in both packs; copper alone uses `produce`, `produced` and `produces`.
- `claim.kind` has 19 distinct values and mixes epistemic status (`estimated_flow`, `reported_structure`, `forecast_context`, `operating_plan`) with content type.
- `Source.review_status` (7 values, for example `government_analysis_read_via_web`) combines source class with retrieval method and is typed by hand.
- All 44 claims have `review_status = manually_source_checked_candidate` and `ground_truth = false`.
- Metrics carry `source_ids` but no `entity_id`. Entities carry no significance or rank field.
- Only 7 of 17 fetchable HTML excerpts in the oil pack matched their cited page verbatim (details in `docs/data-acquisition.md`).
- No acquisition code exists. No LICENSE file exists at the repository root. `Source.rights` is free text; 4 of 20 oil sources flag unaudited or paid terms.
- The project-local PostgreSQL 17 runtime lists `pg_trgm`, `unaccent` and `fuzzystrmatch` but no `pgvector`, and no PostGIS appeared in the extension listing.
- Review tables (proposals, decisions, accepted versions) are append-only through database triggers. Fixture changes after import stop startup until an explicit migration exists. The migration generator (`scripts/generate-additive-migration.py`) refuses edits and removals and builds SQL by string quoting.
- A hand-drawn Cape of Good Hope route crossed African land in every waypoint variant tried; it was removed. Straight segments between real points cannot represent a curved maritime route.
- A duplicate nested `@cesium/engine` once broke rendering. Lesson: check for nested duplicate dependencies.
- Acceptance cases exist for both packs and have never been executed.

## 3. Non-negotiables

- Observations, reported claims, inference and attributed scenarios stay distinct; a forecast is never relabelled as an observation.
- Provenance and temporal versions are preserved. Review history is append-only.
- Nothing is invented: no fabricated coordinates, figures or quotes. Unknown stays visibly unknown.
- A drawn line must never imply a known vessel, route or shipment unless that is sourced.
- The renderer cannot mutate accepted facts.
- Packs and imports are untrusted data, never code.

## 4. Constraints from the user

- Likely to be open source. Uses open data and some copyrighted articles, so a pack may hold references, hashes, short attributed excerpts and original text, not copies of protected content.
- **Hosting budget:** a hosted version costing more than roughly $10 to $20 a month is not viable. No paid model provider is chosen; nothing here authorises model spend.
- Desktop first. Dark visual style. Tours advance on "next".
- Backend stays Python, FastAPI and PostgreSQL. Frontend becomes TypeScript on a God's Eye View foundation. The corpus will grow to more industries (semiconductors next).
- The user makes their own git commits.

## 5. Workstreams

For each: the question, what is known, the user's leaning if any, and what to deliver. Treat A to D as the foundation because later work depends on them.

**A. Controlled vocabularies and migration.**
Propose closed vocabularies for claim predicate, for epistemic status (separate from content type), and for source class (separate from retrieval method, which the pipeline should record). Base them on the 32 predicates and 19 kinds that actually exist and, where useful, on Wikidata properties (verify each identifier). Provide an old-to-new mapping for all 44 claims. Explain how to migrate without breaking append-only history, the additive migration generator, or existing review records. State how the vocabularies extend to a third industry.

**B. Time model.**
The data has publication, source-as-of, valid-time and recorded dates, with weekly, quarterly and annual cadences mixed. Recommend a temporal model (for example valid time versus record time), how "as of date X" queries would work, and what a timeline control should do when data is sparse or absent. Check what the schema stores today and what is missing.

**C. Conflicting sources.**
The schema has no representation for two claims that disagree. **User leaning:** show an interval instead of a hard number where reports differ, with citations. Evaluate this critically. Considerations to address: differences often come from definitions, scope or vintage, not measurement noise; a min-max range across two sources is not a confidence interval; revisions by one source are not conflicts; non-numeric claims cannot be intervals; averaging silently is forbidden. A likely direction to test: keep individual claims as the record, compute a range only across claims explicitly marked comparable (same definition, unit and period), and otherwise show them side by side. Deliver a data model, a comparability rule, and a display recommendation.

**D. Units and conversions.**
Some figures are in tonnes, some in barrels per day, and the packs forbid silent conversion. Barrels per tonne depends on crude grade. Recommend a unit registry, canonical units per measure type, and how conversion factors are stored as sourced facts. Include currency and period normalisation if relevant.

**E. Real geometry, especially shipping.**
**User leaning:** map the major global shipping lanes from real data, treat them as highways, and draw individual routes as smoothed on-ramps and off-ramps onto them. Evaluate feasibility and design: candidate open datasets and libraries (find them; verify licences, coverage, resolution and update cadence), a graph model with chokepoints and ports as nodes, how alternatives such as Cape versus Suez become different paths instead of straight lines, smoothing method, and storage format (note the PostGIS question). Address the honesty rule: aggregate flows attach to network segments and chokepoints; origin-destination lines imply knowledge that is usually not sourced, so say when they are allowed. Also cover area geometry (strait and region polygons).

**F. Guided tours.**
**User leaning:** curate one tour per major industry, with some form of generation to accommodate updates. Design a chapter data model, how a chapter binds to a globe state (camera, layers, highlighted entities), and how updates work. A direction to test: chapter text cites claim identifiers; numbers are filled from data by slots, never written by a model; when a cited claim is superseded, the chapter is flagged for re-review instead of silently changing. Include a chapter template that covers: what it is and what it is for, current state, where it comes from, how it moves, main players and countries, history, geopolitics, outlook, and where a student might fit. Say which chapters rest on evidence and which are interpretation.

**G. Hosting, cost and identity.**
The user cannot spend more than about $10 to $20 a month and asked how cost scales with traffic. Compare architectures with current, fetched pricing: a static read-only snapshot export (already sketched in `docs/technical-stack.md`), a small VPS with FastAPI and PostgreSQL, and managed services. Identify what breaks the budget (candidates: model calls, third-party map tile terms at public traffic, database hosting), and how bring-your-own-key or local-only chat would keep costs at zero. Address identity: what needs accounts, if anything, for a static public site versus a local install, and how community pack contributions could work through git alone.

**H. Evaluation and trust in model output.**
Turn `acceptance-cases.json` into an executable evaluation design that needs no paid model to start. Define deterministic gates for model proposals (verbatim excerpt substring, numbers present in the excerpt, schema validity) and how to measure retrieval quality. Recommend which tasks may use model output with checks and which need human review. Confirm or challenge the retrieval note in `docs/technical-stack.md`.

**I. Acquisition pipeline hardening.**
Review `docs/data-acquisition.md` critically. Propose concrete table and file designs for immutable snapshots, retrieval metadata and verification results, handling of script-rendered pages, scanned PDFs and mutable URLs, and the three-state verification (matches, changed, unreachable). Recommend an excerpt policy and how to repair the four reworded excerpts.

**J. Asset and licence audit.**
List every third-party asset in the God's Eye View parts intended for reuse (CSS, fonts, icons, images, bundled data) in `.local/references/gods-eye-view`, with its licence. Verify each; mark unverified ones. Recommend a code licence and a data licence for Nexus and a build-time licence check for packs.

## 6. Deliverable format

Create `docs/recommendations/00-summary.md` and one file per workstream, named `NN-<slug>.md` (for example `01-vocabularies.md`). Each workstream file has these sections, concise:

1. **Recommendation** (at most 10 lines).
2. **Evidence from the repo** (what you checked and how).
3. **Options considered** (a small table).
4. **Migration and compatibility impact**, including the append-only review tables, the additive migration generator and the 44 existing claims.
5. **Risks.**
6. **Effort** (S, M or L) and dependencies on other workstreams.
7. **Decisions needed from the user** (few, phrased so they can answer in a sentence).
8. **Unverified or not checked.**

The summary lists a recommended order of work with a dependency graph, the five most consequential decisions for the user, any contradictions found between documents or between documents and code, and anything important the brief did not ask about.

If time or context runs short, complete A to D and E well before touching H to J, and say which workstreams you did not reach.
