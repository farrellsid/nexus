# Development log

Durable checkpoints for continuing Nexus work across sessions or context limits. This records implementation state and immediate next actions; factual research remains in each investigation's evidence pack.

## 2026-09-22 — Repo initialized; geography visual-base decision recorded

- Initialized the git repository (no prior history existed despite substantial implementation work); made one root commit bundling the existing tree. The user will make their own commits going forward so authorship shows under their account.
- Reviewed the running oil brief in a browser: matches `development-status.md` — 21 entities, 22 assertions, six metric cards, evidence inspector, geography tab. The geography tab's Natural Earth fallback triggered because the test browser reported `MAX_TEXTURE_SIZE` 0 (no usable WebGL), consistent with the already-documented Codex in-app browser case, not necessarily a real-browser regression — unconfirmed in the user's own desktop browser.
- User decision (see `docs/gods-eye-integration.md`): the geography view's visual base, when visual work resumes, should come from God's Eye View's actual dark tactical-HUD design system rather than the current from-scratch minimal styling. Not authorization to restructure the geography layer now — current priority remains route/area geometry and the geographic review model.

## 2026-09-22 — Oil brief and graph integrity

Completed:

- Oil selected as the first complete industry brief; copper retained as the evidence/review fixture.
- Multi-investigation API, PostgreSQL storage, selector, metrics, timeline, reading guide and retained manual review history are live locally.
- Strait of Malacca corrected from an isolated entity to two sourced candidate relationships: aggregate flow to the global system and China's destination share. Migration `003_connect_malacca.sql` preserves the already-imported seed and review history.
- The first connected oil graph had 16 entities and 17 claims. No entity was isolated at that checkpoint.
- Clean checks at that checkpoint: 34 backend tests, 8 browser workflows, TypeScript, Python lint, formatting and production build.

Completed after the initial checkpoint:

- Published briefs now fail validation if any entity is isolated. Synthetic and historical non-brief fixtures may still contain intentional isolates.
- The entity rail displays isolated and one-relationship counts.
- Geography is a separate read-only contract with coordinate, precision, role, reason, caveat, source and check date. It is intentionally outside the PostgreSQL claim-review seed until geographic editing/review is designed.
- First guided geography implemented for Hormuz, Bab el-Mandeb, Malacca and the named industrial port at Yanbu. The initial coordinate plot used sourced label anchors and did not draw shipping or pipeline routes.

Completed after validating the temporary geography:

- Added Suez/SUMED, the Cape of Good Hope route, Sunda Strait, Lombok Strait and the Myanmar-China crude oil pipeline as sourced structural entities.
- Added five candidate relationships covering the Red Sea/Suez connection, the Cape alternative, the Sunda and Lombok alternatives to Malacca, and the Myanmar-China supply corridor.
- Added a 2025-H1 comparison of Malacca, Hormuz, Cape, Suez/SUMED and Bab el-Mandeb flows. These values can overlap within a voyage and must not be summed as unique cargoes.
- Added an authored reading-guide question for alternatives around Malacca and the Red Sea.
- Added `scripts/generate-additive-migration.py`, which rejects changed or removed retained records and generates explicit SQL for additions. Migration `004_expand_oil_routes.sql` applied the new records while preserving review history.
- Corrected migration `004` so it is safely skipped on a fresh database before fixture initialization. The migration runner recognizes the one recorded pre-guard checksum and upgrades it to the guarded checksum without replaying already-applied SQL.
- Current oil pack: 13 sources, 21 entities, 22 claims, 6 developments, 6 metric groups and 11 authored questions. No entity is isolated; 10 currently have one incident relationship and remain candidates for further network growth.

Completed after the God’s Eye View integration review:

- Inspected the current `bilawalsidhu/gods-eye-view` map, viewer, imagery, terrain and credit modules and its MIT/third-party licence boundaries.
- Replaced the temporary coordinate plot with a narrow Cesium viewer adapted from the reusable God’s Eye View seam. It keeps the Nexus workbench as the application shell and supports camera focus from the existing sourced stops.
- Added keyless Esri World Imagery with an OpenStreetMap construction fallback and retained on-map provider credits.
- Added an automatic local Natural Earth map fallback for browsers without a viable Cesium/WebGL context. The Codex in-app browser takes this path; Edge browser tests cover the map surface and its transitions regardless of the selected renderer.
- Retained the evidence boundary: graph edges are not drawn as routes, marker points remain label/facility anchors, and geographic rendering cannot alter reviewed facts.
- Recorded reused and excluded parts in `docs/gods-eye-integration.md` and retained the upstream MIT notice in `THIRD_PARTY_NOTICES.md`.

Next:

1. Add sourced area/route geometry to the real-map layer. Route geometry must have its own evidence and remain distinct from relationship edges.
2. Add a geographic review model before allowing location corrections in the UI.

Validation after guided geography:

- 36 backend tests passed, including clean-database migration and retained-history checks.
- All 8 browser workflows passed, including the guided Malacca-to-alternatives path and narrow layout.
- TypeScript, Python lint, frontend formatting and the production build passed.
- The live API reports four geographic stops, 22 oil claims and zero isolated oil entities.

Validation after real-map integration:

- All 8 browser workflows passed with the Cesium integration and Natural Earth fallback available.
- TypeScript strict checking, frontend formatting and the production build passed.
- Visual inspection in the Codex in-app browser confirmed the Natural Earth fallback, all four labelled stops, stop controls and evidence transition without a visible rendering error.

Research/data cautions:

- The oil pack is curated, not comprehensive or live.
- EIA supplies most current quantitative evidence; broaden source diversity deliberately.
- Aggregate chokepoint flows do not trace individual cargoes.
- A map point must not substitute for a route, country, distributed industry or unknown facility geometry.
