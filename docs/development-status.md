# Development status — 2026-09-22

The user authorized development in `D:/Projects/Nexus` and selected oil as the first complete industry brief. The workbench now opens on an oil brief while preserving the copper pilot as a selectable evidence and review fixture.

## Delivered

- React/TypeScript/Vite interface: investigation selector, entity search, bounded one/two-step schematic graph, relationship selection, evidence inspector, source links and provenance, sourced metric cards, dated events and curated reading guides.
- Guided oil geography with six sourced coordinate anchors (point stops) and two sourced illustrative route corridors (Suez/SUMED, Myanmar-China pipeline), explicit point precision, an explicit approximate-corridor caveat on routes, and direct transitions back into the evidence graph. Route geometry is sourced from real anchor coordinates, kept visually and architecturally distinct from relationship-graph edges, and does not map distributed/country entities to arbitrary centroids. A Cape of Good Hope route was attempted and removed: every real-waypoint chain tried still drew a line visibly crossing African land, which is inherent to approximating a curved maritime route with straight segments between real charted points, not a data error — see the 2026-09-22 log entry. **The Cesium globe itself currently falls back to the local Natural Earth map on every tested browser** (a real, unresolved rendering bug, not a GPU/driver issue — see log); the narrow Cesium viewer/source path adapted from God's Eye View is implemented but not currently rendering.
- Python/FastAPI API with validated fixture import and explicit domain ownership.
- Oil brief for 2025-Q3 through 2026-Q2, with selected structural baselines and developments through 2026-09-10: 20 public source records, 23 entities, 26 source-checked candidate assertions, 8 developments, 11 metric groups and 14 authored questions. Estimates, reported values, forecasts and unknowns remain distinct. Source diversity now includes IEA and India's PPAC alongside EIA.
- An expanded chokepoint network connects Malacca to Sunda, Lombok and the Myanmar-China pipeline, and connects Bab el-Mandeb/Suez to the Cape alternative. A pre-disruption comparison keeps overlapping route totals explicit and warns against summing them.
- An additive migration generator compares a proposed fixture with the retained database seed, refuses edits or removals, and emits a reviewable SQL migration for additions. Migrations `004_expand_oil_routes.sql`, `005_deepen_oil_baseline.sql` and the hand-written `006_sync_oil_acceptance_questions.sql` carry these expansions without replacing review history.
- Multi-investigation PostgreSQL migration and case-scoped reads, while retaining append-only review history.
- PostgreSQL-backed candidate review, rejection and correction workflow. Accepted versions, decisions and proposals are retained separately; stale or conflicting reviews return a conflict instead of overwriting state.
- Review UI with reviewer/reason fields, evidence/date correction controls, pending proposals and complete version/decision history. Attribution is explicitly self-reported rather than authenticated.
- Project-local PostgreSQL 17 development runtime, transactional checksum migrations and native backup/restore commands. Secrets, data, logs and archives remain under ignored `.local/` paths.
- OpenAPI-generated frontend types. Runtime validation happens in the API at fixture and response boundaries; the browser trusts that local API contract.
- Published-brief validation rejects isolated entities; the UI reports isolated and one-relationship counts. Isolated synthetic invariant tests, real-fixture API checks, executable import-boundary checks and browser workflows remain separate.
- Local startup script, dependency lockfiles and a Windows CI definition.

The copper research fixture and acceptance-case files were not edited. The oil fixture is stored separately under `investigations/02-oil-system`. The UI reuses authored expected answers as explicitly curated guides. Passing deterministic UI checks is not an LLM evaluation and does not establish source truth or entailment.

## Validation performed

- 36 backend tests passed. These include oil schema/reference and geography checks, fresh-database additive migration behavior, published-brief isolation prevention, multi-investigation isolation, real PostgreSQL concurrency, rollback, idempotency, rejection, immutable history and native backup/restore checks using disposable schemas/databases.
- All 8 browser workflows pass, including oil metrics, investigation switching, narrow layout, evidence exploration, unavailable-service handling, review persistence and concurrent-review conflict handling.
- TypeScript strict check and the production build passed after the real-map integration. Python lint and frontend formatting checks passed.
- Visual inspection confirmed the in-app browser automatically falls back from an unsupported Cesium WebGL context to the Natural Earth map without losing stop selection or showing the render failure.
- Browser testing found an entity-switching crash caused by rendering a new center against the previous graph. Clearing the graph during selection fixed it; the workflow now checks browser errors too.

Dependency notes: FastAPI's installed test transport emits two upstream deprecation warnings (httpx and an AnyIO alias). Tests pass; revisit them when updating the lockfile. The sandbox blocked dependency downloads and browser/compiler subprocesses; approved local development execution completed these checks.

## Next increments

1. ~~Add sourced area/route geometry.~~ Done for Suez/SUMED and the Myanmar-China pipeline (2026-09-22); the Cape of Good Hope route was attempted and deliberately removed rather than shipped misleading.
2. ~~Deepen the oil baseline~~ (2026-09-22): stocks, refining capacity and two more producer/consumer series added.
3. **Fix Cesium globe rendering** (2026-09-22 investigation, unresolved). Reproduces identically across two different browser engines and after ruling out GPU/driver, network, and every Cesium `Viewer` option tried — a real, deterministic bug, not an environment issue. Needs a proper brainstorm/plan before attempting a fuller port of God's Eye View's `MapStackController` (imagery/terrain lifecycle management), since matching just its `Viewer()` options did not fix it. See the 2026-09-22 log entry for the full list of ruled-out causes.
4. Add a geographic review model before allowing location corrections in the UI.
5. Add evidence-bounded generated answers with citation/unknown/conflict evaluation and a separately chosen model budget.

No model provider, paid usage, live ingestion, schedule or deployment was set up. Reviews remain manual; there is no automatic claim acceptance, contradiction adjudication, PDF parser or as-of replay. The current metric cards are compact comparisons, not a general charting subsystem. Google Photorealistic 3D Tiles and Cesium ion were deliberately excluded because they require separate credentials and provider terms.
