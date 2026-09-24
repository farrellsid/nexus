# Development log

Durable checkpoints for continuing Nexus work across sessions or context limits. This records implementation state and immediate next actions; factual research remains in each investigation's evidence pack.

## 2026-09-24, M5 phase B in progress on branch m5-shell

Commits so far: B1 (Node server, Pinokio, QA scripts), A1c (correction, see below), B2 (voice and the HUD's AI summary), B3.1 cables, B3.2 first-run launcher (moved forward from B14), B3.3 earthquakes, B3.4 bikeshare, street traffic and transit. Layer count 21 to 16; unit tests 3600 to 2945, all passing; smoke passes with an empty `known-errors.json`. `apps/shell/UPSTREAM.md` has one row per step.

**Correction found in B2:** `.gitignore` excluded all of `src/data/`, which also holds 236 source and test files, so A1 never put them in history. Narrowed to `src/data/local_data/` and `src/data/fixtures/` and tracked the code (row A1c). The untouched reference remains `.local/references/gods-eye-view` at `f01b6a5`.

**Method that works:** delete a layer's directories and data modules, run `node scripts/nexus-dead-modules.mjs` (it lists dangling imports, which are exactly the consumers to edit), then `grep` for the layer's string ids and role names, then fix tests. `scripts/nexus-prune-config.mjs` removes names of deleted modules from `package.json` exports, `package-boundaries.json` and `format-scope.json`. Step verification: unit tests, dead-module baseline (`--record` after reviewing new unreachables), boundaries, one `@cesium/engine`, `vite build`, Playwright smoke.

**Remaining order (dependency-driven):** radio, directions, ALPR, CCTV, satellites and launches, awareness, installations and FIRMS (FIRMS's `anchors` service is used by installations, so installations go first), vessels, military and flights with the aircraft cockpit, then B11 to B16. Layer-registry tests use surviving ids (`local-dams`, `local-datacenters`, `radio`) as stand-ins and need those swapped as layers go; B13 removes the last real layers and those tests get Nexus ids. **Not yet done:** phase C (TypeScript additions) and phase D (`check_shell.py`, licence components, user check in Edge).

## 2026-09-24, M5 phase A done on branch m5-shell

Branch `m5-shell` (three commits so far: A1, A1b to A4, A5), never `master`, per the user's answer. `apps/shell/UPSTREAM.md` is the step log. Imported the God's Eye reference (`f01b6a5`) as code only; its datasets, models and event media are on disk but gitignored so they never enter history. **Baseline:** 4168 upstream tests, 4158 pass, 0 fail, 10 skipped (identical to the untouched clone, after I corrected my own mistake of excluding `build/`, which is source, and `docs/*.md`, which 23 tests read); one `@cesium/engine` (22.3.0); `vite build` 423 files, 31.2 MB. **Step checks added:** `npm run check:step` (tests, dead-module checker with a recorded baseline, one-engine check, Playwright smoke with a shrink-only known-errors list and an allowed-hosts list). **A5:** removed the Google Fonts and Material Symbols CDN dependency (189 KB of local woff2, OFL and Apache-2.0); the look was checked by screenshot against the baseline and one cascade-order difference (smaller arrows) was found and fixed. The page now contacts only localhost, Esri imagery and the Re:Earth terrain service. **Next:** phase B, the strip steps B1 to B16.

## 2026-09-24, M5 plan drafted

Wrote `docs/superpowers/plans/2026-09-24-m5-visual-shell.md` after measuring the God's Eye clone (`.local/references/gods-eye-view`, commit `f01b6a5`). Nothing is built. Awaiting the user's answers on four decisions (strip-step recording, JS versus TS, local imagery, effects). The EIA binding work is staged for the user's commit.

## 2026-09-24, EIA binding applied

Uncommitted (staged for the user). At the user's request, added measurement-level source bindings: `SourceBinding` on `MeasurementRecord` (additive, default empty), a validator rule (bound source must exist, needs a basis, no repeats), `measurement_source` (migration `012_measurement_sources.sql`, append-only), storage read and write, and the readers (comparability reports and the evaluation corpus add bound sources to the group's). Release `nx-norm-2026-09-24-r3` binds O-M07 (3 points) to O-S28, O-M09 (2) to O-S29 and O-M08 (2) to O-S30, each with a basis that says it is the same publisher and survey. Applied to the real database after a backup (`.local/backups/nexus-20260924-073804-b5330d.dump`); r3 accepted by `farrellsid`; claims, proposals, decisions, versions and sources unchanged. 454 backend tests pass. **Next:** M5 (visual shell) or another priority the user names.

## 2026-09-24, EIA registered and the other adapters

Uncommitted. Registered EIA series O-S28 to O-S30 (migration 011, release r2 accepted by `farrellsid` on the user's direction, baselines, verified), added JSON extraction, key injection for the EIA host only, StatCan, Sodir and GDELT parsers, `scripts/collect.py` and the results in `docs/acquisition-providers.md`. 446 backend tests, ruff, licence gate (dev and release) and `normalise.py check` pass. Backup before the migration: `.local/backups/nexus-20260924-071615-950804.dump`. **Next actions:** the user directed that we work with the data we have and target gaps later; binding measurements to O-S28 to O-S30 is deferred for consideration. Everything from this session's data-source work was staged for the user's commit. Next: M5 (visual shell) or another priority the user names.

## 2026-09-24, provider adapters, cross-check and source survey

Uncommitted. Built `backend/app/acquisition/providers/` (eia, jodi, compare, crosscheck, observation), URL and error redaction in `policy.py` and `fetch.py`, `scripts/crosscheck.py`, `docs/crosscheck-report.md`, and the survey in `docs/acquisition-providers.md`. Verified: the key appears nowhere in 166 files, the stored objects or the database; the real cross-check gave 7 equal, 8 no observation, 0 differing; JODI has no Iraq, Russia or Iran crude production for 2026. Five response objects are under `.local/objects/` (git-ignored). **Next actions:** the user answers the open decisions in `docs/acquisition-providers.md` (register provider series as sources, next adapters, GDELT, China); then either continue data sources or start M5.

## 2026-09-24, M4 built and applied

**Applied after the user's approval:** providers EIA and JODI; every source `store`; EIA key saved in `.local/eia-api-key.txt` (git-ignored, never printed); migration 010 applied to the real database (backup `.local/backups/nexus-20260924-064804-f1f23b.dump`, recorded history identical, no acquisition rows yet). M3 is applied (migration 009). The M3 files were staged for the user's commit; M4 files are unstaged.

- Plan: `docs/superpowers/plans/2026-09-24-m4-acquisition-pipeline.md` (with an "As built" section).
- Built: `backend/app/acquisition/` (policy, fetch, snapshots, extraction, verification, proposals), `backend/app/storage/migrations/010_acquisition.sql`, `backend/app/storage/acquisition.py`, `scripts/acquire.py`, `snapshot_policy` in `licences/source-rights.json` and the licence gate, `docs/acquisition-providers.md`.
- Verified: 382 backend tests (none uses the network), ruff, licence gate; migration 010 rehearsed on `nexus_rehearsal_m4` with two real fetches, recorded history identical, no object files written.
- Found: raw byte hashes of two EIA pages matched in 1 of 4 comparisons while extracted-text hashes matched in 4 of 4; providers sampled (EIA needs a key, JODI CSV is keyless with terms unread).
- **Next actions:** the user decides providers, storage policy per publisher and terms, then back up and apply migration 010 to the real database. The 13 M0 proposals still await a reviewer and the eval oracles await confirmation. After M4 the roadmap moves to the UI track (M5) or M6 data work. Scratch databases `nexus_rehearsal_m0`, `m2`, `m3`, `m4` can be dropped.

## 2026-09-24, M3 done and applied

**Applied after the user's approval:** backup `.local/backups/nexus-20260924-061617-b23ae7.dump`, migration 009 applied, recorded history and normalisation hashes identical, `/api/comparisons` returns `[]`. The classes and the comparability rules are approved; no oracle is marked `user_confirmed` yet. Nothing is committed since the four commits.

- Plan: `docs/superpowers/plans/2026-09-24-m3-evaluation-and-comparability.md` (with an "As built" section).
- Built: `backend/app/evaluation/` (cases, figures, corpus, retrieval, answers, oracle), `backend/app/comparability/` (model, display, reports), `backend/app/storage/migrations/009_comparability.sql`, `backend/app/storage/comparisons.py`, two read endpoints, `scripts/evaluate.py`, `evals/industry-v1/suite.json`, `docs/evaluation-oracle-review.md`. OpenAPI and types regenerated (additions only).
- Verified: 273 backend tests, ruff, `tsc`, prettier, 8 of 8 browser workflows; migration 009 rehearsed on `nexus_rehearsal_m3`; the evaluation run is deterministic.
- Found: eight oracle findings (`docs/evaluation-oracle-review.md`, F1 to F8), mostly stored values with no retained passage.
- **Next actions:** the user confirms the 26 expected answers and classes, approves the comparability rules and confirms they are the only reviewer. Then back up and apply migration 009 to the real database, mark confirmed cases `user_confirmed` in the suite (and update the count test), and decide whether to fix F1 (Q05) and F2 (O-Q05) as corrections. Scratch databases `nexus_rehearsal_m0`, `m2` and `m3` can be dropped. Then M4 (acquisition), which repairs the unanchored values.

## 2026-09-24, M2 done: release accepted

**Applied after the user's approval:** backup `.local/backups/nexus-20260924-055016-8c76d4.dump`, migration 008 applied, release `nx-norm-2026-09-24` recorded and accepted (reviewer `farrellsid`, recorded from the user's chat approval). Recorded history unchanged (57 proposals, 0 decisions, 0 versions). Nothing is committed. The entries below describe the build. M0 is applied (see the entry below) and its 13 proposals await a reviewer.

- Plan: `docs/superpowers/plans/2026-09-24-m2-evidence-model-foundations.md` (with an "As built" section listing deviations).
- Built: `normalisation/vocabulary-v1.json`, `normalisation/releases/2026-09-24.json`, `backend/app/normalisation/` (vocabulary, release validator, measurement reader, digest), `backend/app/storage/migrations/008_normalisation.sql`, `backend/app/storage/normalisation.py`, four read endpoints in `backend/app/main.py`, `scripts/normalise.py`, `scripts/render_normalisation_review.py`, and the review sheet `docs/normalisation-review.md`. OpenAPI and frontend types regenerated (additions only).
- Verified: 173 backend tests, ruff, licence gate, `tsc`, 8 of 8 browser workflows; rehearsal on `nexus_rehearsal_m2` (a restored copy of a fresh backup) left every recorded-history table hash identical; the release recorded twice without duplicates. Afterwards, at the user's direction, Russia and Iran were added to the release (45 entities); the `check` passes.
- Found: the copper claims C11 and C13 have retained excerpts that are fragments not stating the claim ("to the Aurubis Group", "are expected to arrive in May"), although the cited pages do support both. Verbatim is not the same as supporting. Added to the deferred copper audit; not fixed.
- **Next actions:** the 13 M0 proposals still await a reviewer. Any mapping change needs a new release (edit the JSON, `normalise.py check`, re-render the sheet, record, decide); it must keep every accepted entity and alias. Scratch databases `nexus_rehearsal_m0` and `nexus_rehearsal_m2` can be dropped. Then M3.

## 2026-09-24 — M0 built and rehearsed; awaiting approval

**Applied 2026-09-24 after the user's approval:** backup `.local/backups/nexus-20260924-044805-5c5d7f.dump`, migration 007 applied (41 sources), 13 proposals recorded (57 total, 0 decisions, 0 versions). Nothing is committed.

- Added `scripts/verify_excerpts.py`, `investigations/excerpt-exceptions.json`, `scripts/propose_evidence_repairs.py`, `investigations/02-oil-system/repairs/2026-09-24-oil-evidence-versions.json`, `backend/app/storage/migrations/007_repair_oil_evidence_versions.sql`, seven new sources O-S21 to O-S27 in the oil pack, rights entries for them, and a coverage label of 2026-09-16.
- Rehearsed on `nexus_rehearsal_m0`, a restored copy of a fresh backup (`.local/backups/`): migration added 7 evidence sources and changed no history rows; the 13 proposals were recorded (44 to 57); a rerun added none; the API started; the real database is unchanged (44 proposals, 0 versions).
- 98 backend tests pass; the licence gate has 0 errors; the oil excerpt verifier has 0 failures. `docs/recommendations/repo-audit.py` fails ruff (another agent's file; left alone).
- **Next actions:** a reviewer accepts or rejects the 13 pending proposals in the review panel; drop the scratch database `nexus_rehearsal_m0` when no longer wanted; then M2.

## 2026-09-23 — Design records: rebuild, acquisition, packs, methodology

No code changed. Design discussion with the user produced these records, each marking what is the user's decision and what is an assistant proposal:

- `docs/frontend-rebuild.md`: rebuild on a God's Eye View foundation (user decision), industry/investigation container and shared entity registry, two-level type taxonomy from prior-art research, action-layer principle, phasing, warning vocabulary for missing data, and the user's guided-tour requirements.
- `docs/data-acquisition.md`: no acquisition code exists. An excerpt check found 7 of 17 fetchable HTML excerpts verbatim; the rest are reworded, unreproducible or drifted. Proposed pipeline: acquire, extract, review, refresh.
- `docs/data-packs.md`: installable industry packs, licensing and pack-security proposals. No LICENSE file exists at the repository root.
- `docs/methodology.md`: orientation document for how Nexus works, including two gaps verified in the data: 32 distinct free-text predicates across 44 claims, and `claim.kind` mixing epistemic status with content type.
- `docs/technical-stack.md`: retrieval note. The local PostgreSQL runtime has `pg_trgm` and `unaccent` but not `pgvector`; vectors deferred until acceptance cases show a need.
- `docs/briefs/technical-design-review-brief.md`: a brief for a separate, higher-tier agent to write recommendations on vocabularies, time, conflicting sources, units, shipping geometry, tours, hosting cost, evaluation, acquisition and licences. It writes only to `docs/recommendations/`.
- **M1 finished 2026-09-24** (holder `farrellsid`; `LICENSE` MIT and `LICENSE-CONTENT.md` CC BY 4.0 written; release gate 0 errors; `Zlib` allowed; copper publisher audit deferred to data expansion). **M0 started.**
- **M1 started** (rights and licence gate). Built `scripts/check_licences.py` test-first (24 tests) and `licences/` manifests. Independently read the primary licence texts for God's Eye (MIT, holder Bilawal Sidhu, third-party assets excluded, local copy identical to upstream), Inter and JetBrains Mono (OFL 1.1), the icon repository (Apache-2.0), Cesium (Apache-2.0), Natural Earth (public domain), Wikidata ("All data in Wikidata has a CC0 license") and EIA (public domain, acknowledgement requested, third-party material excluded). The gate found its own first bug: nested npm packages were read from the wrong path. Real findings: pako is `(MIT AND Zlib)`, zlib terms are in its file headers, so `Zlib` was added to the allow-list. Release mode fails only on the missing `LICENSE` and `LICENSE-CONTENT.md`. Full suite 62 passed after starting the local database. Zero accepted versions exist in it.
- `docs/roadmap.md`: proposed milestones M0 to M11, a Data track and a UI track merging at M6, each with [T] automated, [A] assistant and [U] user verification.
- `docs/decisions.md`: new decision log. Recorded after the review: cap of CAD 10 to 20 a month; versioned normalisation with aliases; side-by-side sources; modelled shipping alternatives; static public snapshot with local authoring; MIT and CC BY 4.0; published tours use accepted versions only. Consequence: nothing is publishable until claims are accepted.
- `docs/recommendations/`: the separate agent's ten recommendations (see `00-summary.md`). Spot-checked eight of its findings against the repo; all held. Three were corrections to earlier statements here: the excerpt diagnosis was wrong for two of four sources (O-S05 and O-S07 omit "(b/d)", O-S08 and O-S10 expand it), O-C26 is not supported by its retained excerpt, and the Cape failure was a limit of the waypoint chains I tried, not an inherent limit of drawing routes. Also confirmed: corrections cannot change a claim's predicate, migrations 002 to 006 disable the seed trigger, and the oil pack's 2026-09-10 cutoff label is contradicted by later evidence. README counts fixed. Data repairs need the user's go-ahead.
- `docs/ui-flows.md`: first-pass UI flows (one persistent shell, screens, Mermaid flows, action verbs, degradation). User decisions recorded: dark style, globe behind other screens, "next"-driven tours, desktop first.

Next: no implementation is scheduled. Open questions are listed at the end of each record.

## 2026-09-22 — Cesium rendering bug SOLVED: duplicate `@cesium/engine` in the dependency tree

**Root cause: two copies of `@cesium/engine` were installed, producing two `ContextLimits` singletons.**

`cesium@1.138.0` depends on `@cesium/engine@^22.3.0` *and* `@cesium/widgets@^14.3.0`. npm resolved `@cesium/widgets@14.5.0`, which requires `@cesium/engine@^24.0.0` — an incompatible major. npm therefore hoisted engine **22.3.0** for `cesium` and nested engine **24.0.0** inside `@cesium/widgets/node_modules/`. `Viewer` (from widgets) wrote `ContextLimits._maximumTextureSize = 16384` into one copy; `ImageryLayer`/`Texture` (from the hoisted copy, reached via `cesium`) read `0` from the other copy's untouched initial value. Hence `DeveloperError: Width must be less than or equal to the maximum texture size (0)` while the live WebGL context was perfectly healthy.

**Fix**: `"overrides": { "@cesium/widgets": "14.3.0" }` in `apps/web/package.json` — 14.3.0 requires engine `^22.3.0`, matching the hoisted copy. This is the same resolution God's Eye View has. Verified: dep bundle dropped 19.3 MB → 10.2 MB, `_maximumTextureSize` occurrences 6 → 3, and exactly one `ContextLimits.js` module marker remains. **The Esri satellite globe now renders**; the Natural Earth fallback is no longer triggered. Watch for regression whenever Cesium is upgraded — check for a nested `node_modules/@cesium/widgets/node_modules/@cesium/engine`.

**How it was found**, after a long unsuccessful stretch of guessing at Cesium `Viewer` options:
1. A bare, React-free HTML+Cesium page reproduced the bug with zero Nexus code — ruling out React, our component, effect lifecycle and container sizing.
2. Running that *same probe file* inside the God's Eye View project survived, while it failed in Nexus — proving the problem was the project environment, not our Cesium usage.
3. Bisecting the environment ruled out the React plugin, the tsconfig, Cesium's static worker assets, `vite-plugin-cesium`, and the Vite major version (6 vs 7 both fail).
4. Comparing the two served dep bundles showed Nexus's was ~2× the size with exactly 2× the occurrences of `_maximumTextureSize` — which located the duplicate module immediately.

Things previously suspected and now definitively **not** the cause: GPU/driver (the user's real Edge reported a healthy 16384 context), network reachability to tile servers, `msaaSamples`, `contextOptions`/`preserveDrawingBuffer`, `requestRenderMode`, `globe.show` sequencing, Vite's dep cache, and the Cesium version itself.

Also in this change: removed `import "cesium/Build/Cesium/Widgets/widgets.css"`. It was not the cause, but it is redundant — `vite-plugin-cesium` injects `/cesium/Widgets/widgets.css` in both dev and production (verified in `dist/index.html`, asset copied to `dist/cesium/`), and God's Eye does not import it either. This also removes a second entry point into `cesium/Build/*`.

Validation: 38 backend tests, 8/8 browser workflows, `tsc --noEmit`, production build and Prettier all pass.

## 2026-09-22 — Cape route removed, label collision fixed, Cesium rendering investigated (was unresolved, see entry above)

User review of the geography tab (screenshots, not just automated checks) surfaced three real problems the parallel agents' own tests hadn't caught.

**Cape of Good Hope route line removed** (`investigations/02-oil-system/geography.json`, `backend/tests/test_workbench.py`): the originally shipped straight 2-point line (Bab el-Mandeb → Cape of Good Hope) cut directly across the African interior — mathematically exactly what the sourced coordinates imply (verified by reconstructing the d3 projection and inverting the rendered path), but visually indistinguishable from a bug. Tried three increasingly elaborate real-waypoint fixes, each verified by sampling ~50 points per segment against the actual land polygon (not just eyeballing screenshots):
1. Added Cape Guardafui + Cape Sainte Marie (Madagascar) + Cape Agulhas as real Wikidata-sourced waypoints: cut land-crossing from ~35% of the line's length to ~13%, but the approach to Madagascar visibly clipped the island itself, and a great-circle interpolation between the original two endpoints alone (no waypoints) was no better (still 100% over land — Africa sits almost exactly on the geodesic between the two points).
2. Added Cape Recife as a further waypoint: eliminated the mid-continent cut entirely (0% land-crossing on two of four segments), leaving only brief unavoidable stretches right at real headlands/the Cape Flats isthmus.
3. Concluded this is a structural limit, not a research gap: real capes are themselves small landforms, and no chain of real charted points fully avoids touching land while representing a route that must go *around* a continent. Removed the drawn line entirely (`geography.json` routes array now has 2 entries, not 3); the entity, its role and its relationship to Bab el-Mandeb (claim `O-C19`) remain fully explorable via the relationship graph, just without a misleading map line. Updated the two backend tests that asserted a 3rd route/`oil-cape-good-hope` route entity.

**Map label collision fixed** (`CesiumGeographyMap.tsx`): stops close together (Malacca/Sunda/Lombok) had permanently-visible text labels that overlapped illegibly. Now only the selected stop shows its label (both in the SVG fallback and the Cesium renderer, via `label.show`); other stops show just their numbered marker with the name as a native tooltip (`<title>`). No functionality lost — the sidebar already lists every stop's full name.

**Cesium globe rendering — investigated at length, root cause not found.** The user's real Edge browser (confirmed real Intel UHD + NVIDIA RTX 3050, not a VM) shows the exact same `DeveloperError: Width must be less than or equal to the maximum texture size (0)` inside `ImageryLayer._createTextureWebGL` that this session's sandboxed browser shows — reproducible, deterministic, not environment flakiness. Ruled out with real tests, each independently verified rather than assumed:
- **GPU/driver**: user ran a one-line devtools check in their own Edge — plain `canvas.getContext('webgl2')` reports `MAX_TEXTURE_SIZE: 16384` (healthy) even though Cesium still fails the same way. Not a hardware/driver problem.
- **Network reachability**: `curl` to both `services.arcgisonline.com` and `tile.openstreetmap.org` succeeds fine.
- **`msaaSamples: 4`**: removed, no change.
- **`contextOptions: { webgl: { preserveDrawingBuffer: true } }`**: the one real config difference found versus God's Eye View's own `createApplicationViewer()` (`.local/references/gods-eye-view/src/app/viewer.js`, read directly for comparison) — added, no change.
- **`requestRenderMode`** (on-demand vs. continuous rendering, the other structural difference from their bootstrap): removed, no change.
- **Stale Vite dependency cache**: full `node_modules/.vite` wipe and dev-server restart (fresh dependency-optimization hash confirmed in the reload), no change.
- **Cesium version** (we're on 1.138.0, they're on 1.124.0): attempted downgrade broke dependency resolution (1.124's `@cesium/engine`/`@cesium/widgets` split wants a different `@zip.js/zip.js` than what's installed) before it could even be tested; reverted cleanly to 1.138.0 (`package.json`/`package-lock.json` confirmed unchanged via `git diff`).

Diagnostic finding worth preserving: reading `viewer.scene.context._gl` directly right after `new Viewer()` shows a genuinely healthy context (`maxTextureSize: 16384`, `isContextLost: false`) — the degeneration happens a few seconds later, specifically when the first real imagery tile texture is created. That rules out a container-sizing race at construction time. Current `CesiumGeographyMap.tsx` state: `msaaSamples` removed, `requestRenderMode`/`maximumRenderTimeChange` removed (continuous rendering, matching God's Eye View), `contextOptions.preserveDrawingBuffer` added — none of these fixed it, but they're a strict simplification toward the known-working reference and were left in rather than churned back.

**Also discovered while testing**: the local reference clone at `.local/references/gods-eye-view` was checked out with `git sparse-checkout` limited to `src/app`/`src/data`/`src/maps`/`src/ui` (46% of tracked files) — missing `server/`, which its own `vite.config.js` requires, so it couldn't even start. Ran `git sparse-checkout disable` to materialize the full tree; it now runs (`npm ci && npm run dev`, opens on `:4173`) and its Cesium globe renders successfully in the same sandboxed browser where ours fails, which is the strongest evidence this is a real code bug in our integration, not an unfixable environment limitation.

**Next**: the user asked to scope the real fix — porting God's Eye View's `MapStackController` (imagery/terrain lifecycle management with caching, `src/maps/controller.js`) rather than more `Viewer()` option tweaking, since matching their options alone didn't work. This needs its own brainstorm/plan before implementation, not a quick patch.

## 2026-09-22 — Route/area geometry and a deepened oil baseline (parallel agents)

Two independent background agents worked concurrently on disjoint files, then their combined output was independently re-verified (not just taken on their word): `pytest backend/tests -q` (38 passed), `ruff check`/`ruff format --check` (clean), `npm run format:check` and `npm run build` (clean), and the full `npm run test:e2e` suite (8/8) all pass against the final combined state.

**Route/area geometry** (`backend/app/geography.py`, `investigation.py`, `investigations/02-oil-system/geography.json`, `CesiumGeographyMap.tsx`, `GuidedGeographyView.tsx`):

- Added a `routes` geometry type alongside the existing point `stops`, each with its own source, precision and an explicit "approximate illustrative corridor, not an as-built route" caveat. Kept architecturally and visually distinct from the separate relationship graph.
- Closed the geography gap for entities that already existed in the knowledge graph but had no map anchor: two new point stops (Sunda Strait, Lombok Strait) and three sourced corridors (Suez Canal/SUMED, Cape of Good Hope, Myanmar-China pipeline). All coordinates came from Wikidata pages fetched and read directly, not invented.
- Both the Cesium renderer and the Natural Earth SVG fallback draw the same route geometry, rendered dashed and distinct from point markers.
- Regenerated `contracts/openapi.json` and `apps/web/src/generated/api.ts` through the documented commands rather than hand-editing them.

**Deepened oil baseline** (`investigations/02-oil-system/evidence-pack.json`, `acceptance-cases.json`, `README.md`, migration `005_deepen_oil_baseline.sql`):

- Added five new metric groups (O-M07–O-M11): U.S. commercial crude stocks, U.S. refinery capacity, U.S. refinery utilization, India crude imports, and per-country OPEC+ August 2026 production (Saudi Arabia, Iraq, Russia, Iran individually, not just the aggregate group).
- Diversified sourcing beyond EIA: added IEA's Oil Market Report and India's PPAC monthly reckoner as new source categories, with excerpts fetched and read directly (the PPAC table came from a scanned PDF, read via table extraction, not estimated).
- Added two new entities (India, Iraq) and four new claims so nothing is graph-isolated, plus two new events, three new acceptance-case questions, and generated the additive migration via `scripts/generate-additive-migration.py`.
- Oil pack now: 20 sources, 23 entities, 26 claims, 8 events, 11 metric groups, 14 authored questions.

**Known pre-existing issue surfaced, not fixed:** `scripts/start-local.ps1`'s readiness probe timed out twice against already-healthy uvicorn/vite processes during this work (likely too tight under concurrent load), causing the script to kill healthy processes. Worked around manually; the script itself still needs a longer or more tolerant readiness check.

**Leads for later** (sourced but not pursued, to avoid overscoping this pass):

- Saudi East-West and UAE Abu Dhabi (Habshan-Fujairah) pipelines are likely sourceable the same way the new routes were.
- SUMED could become its own entity/route — Ain Sokhna and Sidi Kerir coordinates are already sourced from this pass.
- Permian Basin could get a real boundary polygon (not just a point) from Wikidata/EIA — a genuine "area" geometry candidate.
- IHO's Limits of Oceans and Seas publishes actual strait boundary polygons, which could upgrade Hormuz/Bab el-Mandeb/Malacca from label points to sourced areas.
- PPAC Table 8 has India refinery-level capacity by company; IEA's OMR preview likely has more OPEC+ members freely readable than the four pulled; OPEC's own MOMR is paywalled (HTTP 402) so was not used as a primary source; EIA has a dedicated China/US/Japan strategic-reserve article distinct from the commercial-stocks series added here; EIA STEO has a global (not just U.S.) inventory series but as a draw rate rather than an absolute level.

**Follow-up fixes after user review (same day):** the user viewed the rendered geography tab and flagged the Cape of Good Hope route as visually wrong. Investigation (not just re-running the agent's tests, which were text/DOM assertions and hadn't caught this):

- The straight 2-point line between Bab el-Mandeb and Cape of Good Hope was mathematically exactly what the sourced coordinates imply (verified by reconstructing the same d3 projection and inverting the rendered path back to lon/lat) — but a straight line between those two real points cuts directly across the African interior, which looks broken even though the coordinates are correct. Fixed by adding four more real, sourced waypoints (Cape Guardafui, Cape Sainte Marie on Madagascar, Cape Recife, Cape Agulhas — all fetched from Wikidata, not invented) chosen to keep the line over open water. Verified with a rigorous point-sampling check against the actual land polygon (not just visual inspection): land-crossing dropped from a continuous ~35% of the line's length (cutting through Kenya/Tanzania/Zimbabwe/South Africa) to isolated short stretches only right at real headlands/islands themselves (Guardafui, approaching Madagascar, and the Cape Flats isthmus between Agulhas and Cape of Good Hope) — a real, disclosed limitation of straight segments between real points, not a bug.
- Separately found and fixed a real data-integrity bug: the oil pack's fixture-vs-database-seed fingerprint no longer matched because `acceptance-cases.json` gained three questions (O-Q12–O-Q14) after migration `005_deepen_oil_baseline.sql` was generated, so the API failed to start ("Fixture differs from the retained database seed"). Root-caused via a full payload diff rather than guessing; fixed with a small hand-written migration (`006_sync_oil_acceptance_questions.sql`) that only refreshes the seed snapshot, since the generator script refuses to run when there are no new sources/claims to insert (there weren't — the referenced claims were already added by 005).
- Also diagnosed, for the user, why Cesium isn't rendering in their real Edge/Chrome despite a capable GPU (confirmed via `Get-CimInstance Win32_VideoController`: Intel UHD + NVIDIA RTX 3050, not a VM) — most likely the browser defaulting to the integrated GPU or a driver blocklist entry; pointed them at `edge://gpu` and the Windows per-app graphics preference setting rather than guessing further.

Next: the geographic review model (docs/gods-eye-integration.md "Later candidates") can now build on a settled geometry schema. The God's Eye View visual-base decision recorded below remains for whenever visual work is scheduled, not now.

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
