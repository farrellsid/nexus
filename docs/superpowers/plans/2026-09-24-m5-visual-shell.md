# M5 Visual Shell Prototype: Plan for Review

> **Status: a plan for the user to approve, not started.** Nothing here has been built. Steps use checkbox syntax so the work can be tracked once approved. Commits: the user makes them unless they say otherwise (see decision 1).

**Goal (roadmap M5):** the God's Eye look, in a shell of our own, before any Nexus data. Dark theme, globe behind everything, static corner readouts, an action-verb skeleton, a 2D fallback, basic share links, and only the current oil stops as fixture data.

**Approach:** start from an unmodified import of `bilawalsidhu/gods-eye-view` (local clone at `.local/references/gods-eye-view`, commit `f01b6a5`), and **strip it in small, tested steps** (your 2026-09-22 direction), then add the few Nexus pieces on top. The Nexus web app (`apps/web`) keeps running untouched until M6 reaches parity.

## What the reference actually is (measured 2026-09-24)

| Fact | Measured |
|---|---|
| Size | 640 JavaScript files, 327 upstream tests (`node:test` `.mjs`), 286 KB of CSS in 11 files |
| Weight | `src/data` 13.6 MB of bundled datasets, `src/layers` 2.9 MB, `public/models` 3.2 MB of 3D models, `public/events` 2.4 MB |
| Language and build | Plain JavaScript (no TypeScript), Vite, no React; a vanilla-DOM shell |
| Dependencies | `cesium`, `satellite.js`, `@mapbox/vector-tile`, `pbf`, `mgrs`, `egm96-universal` (runtime); `vite`, `vite-plugin-cesium`, `puppeteer`, `sharp`, `prettier`, `ws` (dev) |
| Network at page load | `index.html` loads **Google Fonts** (Inter, JetBrains Mono) and **Material Symbols** from Google's CDN |
| Licence | MIT for the code, holder Bilawal Sidhu. Its third-party data and assets are excluded from that grant (cleared list in `licences/components.json`) |
| Node | Requires 24.14 to 25 or 26 and up; this machine has Node 26 |

**What that means:** most of the repository is live-tracking layers, datasets, voice and installer plumbing that Nexus does not want. The look lives in about 250 KB of CSS plus a small set of chrome modules (HUD, split-flap readouts, celestial ring, logo, command dock, scene director, camera verbs, share state). The strip is large, so the plan makes each step small, mechanical and verified.

## Decisions answered by the user, 2026-09-24

1. **Recording:** a dedicated branch `m5-shell`; the assistant commits each strip step there and never on `master`. Because uncommitted work may sit in the index when the branch is created, each M5 commit names its paths so nothing else rides along. Best started after the user commits the pending work on `master`.
2. **Language:** retained upstream modules stay JavaScript; new Nexus code is strict TypeScript; React arrives in M6 as mounted panels.
3. **Imagery:** Esri and OSM for local work; the public build uses Natural Earth through one flag.
4. **Effects (bloom, sensor looks):** still open; decided at the [U] check with screenshots.

## Decisions I needed from you before starting (as asked)

1. **How are strip steps recorded?** The roadmap says a commit per step so the last good state is recoverable. Options: (a) **I commit on a dedicated branch `m5-shell`, never on `master`** (you review and merge or squash it; your commit history on `master` stays yours); (b) I save a dated snapshot of the shell folder before each step under `.local/m5-steps/` and you commit only at milestones. *My recommendation: (a), because 30 to 40 steps is too many to hand-stage, and a branch keeps `master` yours.*
2. **JavaScript or TypeScript for the shell?** Upstream is plain JS with 327 `node:test` tests. Rewriting 300+ retained files to TypeScript would swamp the milestone. *My recommendation: keep retained upstream modules as JS (their tests keep running), write all new Nexus code (action layer, share-link codec, oil fixture, state) in strict TypeScript, and add React only in M6 as panels mounted inside the shell. Nothing about the later evidence UI is blocked.*
3. **Imagery in local development.** Upstream uses Esri's keyless imagery with an OSM fallback. `licences/components.json` marks both as unverified for public use and disables them in a public build (Natural Earth globe instead). *My recommendation: keep Esri and OSM for local work (consistent with your "may not publish" assumption), switch by one flag, and make the public build use Natural Earth.*
4. **Bloom and the "sensor look" effects** (thermal, night-vision style shaders): keep, keep optionally behind a toggle, or drop? This is a judgement on your GPU, so I will leave them in until the [U] check and ask again with screenshots.

## Global constraints

- No live feeds, no voice, no Google Maps or Places, no OpenAI key, no Cesium ion, no photorealistic 3D tiles, no model calls. (`docs/frontend-rebuild.md` strip list, `AGENTS.md`)
- **No third-party network at load.** Fonts and icons are self-hosted; the page makes no request to Google. (Inter and JetBrains Mono are OFL and were read in M1; Material Symbols is replaced by inline SVG so no icon font ships.)
- Exactly one `@cesium/engine` in the dependency tree (the earlier duplicate-engine bug), enforced by a script.
- The public build's emitted files must belong to a cleared component in `licences/components.json` (extended for the shell); upstream `src/data` and `public/models` must not survive the strip.
- A map marker is a sourced label anchor, never a route or a guess; the 2D fallback and the "no fabricated data" rule from the current app must survive.
- Every strip step ends green: upstream tests for retained modules pass, the smoke e2e passes, and a dead-import check finds no dangling reference.
- Reduced-motion is honoured (`prefers-reduced-motion`), and evidence access does not depend on the globe rendering.
- Windows: `PYTHONIOENCODING=utf-8`, write files with the Write tool, `git grep`, not repo-wide grep.

## File structure

| Path | Responsibility |
|---|---|
| `apps/shell/` (create) | The stripped fork plus the Nexus additions; its own `package.json`, Vite config and tests |
| `apps/shell/UPSTREAM.md` (create) | The upstream commit imported, licence notice, and a log of every strip step (what left, why, test result) |
| `apps/shell/src/nexus/actions.ts` (create) | The action-verb layer: `select_entity`, `focus_camera`, `set_layers`, `set_as_of`, `open_evidence`, `go_chapter`, `return_to_tour`, `set_view` (shapes in `docs/ui-flows.md` section 7), with a registry and validation |
| `apps/shell/src/nexus/shareLink.ts` (create) | Encode and decode shell state into a URL hash: industry, mode, chapter, selection, camera, layers; no personal data |
| `apps/shell/src/nexus/oilStops.ts` (create) | The current oil stops and sourced route corridors, generated from `investigations/02-oil-system/geography.json` (real sourced anchors, marked as fixture data) |
| `apps/shell/src/nexus/readouts.ts` (create) | Static corner readouts: as-of date, pack version, "n entities not on map", precision |
| `apps/shell/src/nexus/fallbackMap.ts` (create) | The Natural Earth 2D fallback, ported from `CesiumGeographyMap.tsx` behaviour |
| `scripts/check_shell.py` (create) | Asserts one `@cesium/engine`, no upstream datasets or models in the build, no external hosts in `dist/`, and the emitted files match the cleared list |
| `licences/components.json` (modify) | Add the shell's components (fonts, the adapted upstream code, self-hosted assets) |
| `apps/shell/tests/` (create) | Playwright smoke: renders, canvas has non-blank pixels where WebGL exists, no console errors, the 2D fallback path |

## Phase A: import and baseline (no removal yet)

- [x] **A1. Import unmodified.** Copy the reference (minus `node_modules`, `.git`, `build`) into `apps/shell/` at commit `f01b6a5`; write `UPSTREAM.md` with the commit and the MIT notice. Add `apps/shell` to `.gitignore` exclusions only for `node_modules`.
- [x] **A2. Make it run.** `npm ci` with the `@cesium/widgets` override that fixed the duplicate engine in `apps/web`; run `npm run dev` and load it. Record what fails without keys (expected: several layers and the Google pieces). *Exit:* the globe renders locally.
- [x] **A3. Baseline measurements.** Record the bundle size, the file count, the number of upstream tests and how many pass; record `npm ls @cesium/engine` (must be one).
- [x] **A4. Write the smoke test and the dead-import checker.** The smoke test loads the page and asserts no console errors and a non-blank canvas. The checker walks `import` statements and reports files nothing imports and imports of missing files. Both run after every later step.
- [x] **A5. Self-host fonts.** Replace the Google Fonts and Material Symbols links with local files; the smoke test asserts the page contacts no host outside `localhost` and the imagery providers.

## Phase B: strip, one group per step (each step: remove, run tests, smoke, dead-import check, log in `UPSTREAM.md`)

Order is chosen so each removal has the fewest dependants and the bisection stays cheap:

- [x] **B1. Non-app scaffolding:** `server/`, `pinokio/`, `tools/`, updater and installer scripts, `dev:secure`, dotenv and key-setup panel (keep its graceful-degradation idea).
- [x] **B2. Voice:** `src/voice/` and its tests, the OpenAI realtime plumbing, the microphone chrome. (Keep `actionSchemas.js` as a reference for the action-layer shape, not as code.)
- [x] **B3 to B10. Live layers, one per step:** flights, military flights and awareness, AIS vessels, CCTV, ALPR, radio, traffic and transit, bikeshare, satellites and launches, FIRMS, earthquakes, military installations, submarine cables. Each removal takes its layer file, its tests, its `src/data` datasets, its panel and its catalogue entry.
- [x] **B11. Google Maps and Places, keyless geocoder, directions.** Nexus search is entity search, not geocoding.
- [x] **B12. Annotations and draw tools, detection overlay, contacts roster, the 3D hangar and `public/models`.**
- [x] **B13. Remaining data and events:** `public/events`, leftover `src/data`, the Bhote Koshi scene CSS and other scene-specific assets.
- [x] **B14. First-run and key-setup screens:** keep the loading and first-run pattern, replace the copy and remove the key wizard.
- [x] **B15. Trim the CSS** to the design system that remains (`foundation`, `cockpit`, `controls`, command dock, status, scenes); delete the rest and check nothing references the removed selectors.
- [x] **B16. Final prune:** dead-import checker clean, no orphan tests, `check_shell.py` passes on the build, bundle size recorded against A3.

*Expected outcome:* a shell with the globe, camera, hover, HUD chrome, command dock, scene director, celestial ring, logo and readouts, and nothing that fetches live data.

## Phase C: the Nexus pieces (strict TypeScript, tested with `vitest` or the existing `node:test`, decided in step C1)

- [x] **C1. TypeScript setup for new code only:** `tsconfig` with `allowJs`, `checkJs` off for upstream, strict for `src/nexus/`; choose the test runner for TypeScript.
- [x] **C2. Action layer:** the verb registry with argument validation; the mouse, the scene director and (later) chat all call it. Tests: each verb rejects bad arguments, unknown verbs are refused, and no verb can issue a network request or mutate evidence.
- [x] **C3. Oil stops fixture:** generate `oilStops.ts` from `geography.json` with a test that the generated file matches the source (six stops, two sourced corridors); wire the scene director to fly between them.
- [x] **C4. Static corner readouts:** as-of date, pack version, "n entities not on map", precision of the selection; toggleable, on by default (your 2026-09-23 decision).
- [x] **C5. Share links:** encode and decode the shell state; a round-trip test and a test that a hostile or malformed hash is ignored, not executed.
- [x] **C6. 2D fallback:** port the Natural Earth map and the "no usable WebGL" detection from `CesiumGeographyMap.tsx`; the smoke test forces the fallback path.
- [x] **C7. Global-context mode:** stage a full view and restore the prior state on exit (an upstream pattern to keep), driven through the action layer.

## Phase D: verification against the roadmap exit checks

- [x] **D1. [T]** Smoke e2e green after every step (logged); `check_shell.py`: exactly one `@cesium/engine`, no datasets or models, no external hosts, emitted files match `licences/components.json`; the licence gate in release mode still has 0 errors.
- [x] **D2. [A]** I capture screenshots of the shell and the fallback in my browser, noting that it is a sandbox and not your GPU.
- [ ] **D3. [U]** You open it in your real Edge: judge look and frame rate, decide which effects stay (decision 4), and check reduced-motion behaviour.
- [x] **D4. Docs:** `docs/roadmap.md`, `docs/decisions.md`, `docs/gods-eye-integration.md`, `docs/development-log.md`, `THIRD_PARTY_NOTICES.md`, README.

## Risks and how the plan handles them

| Risk | Handling |
|---|---|
| A 640-file strip breaks something hidden | Small steps, the dead-import checker, the smoke test and the retained upstream tests after every step, a log in `UPSTREAM.md` |
| Removing a module silently changes the look | Screenshot after B2, B10, B14 and B15, compared with the A2 baseline; you judge at D3 |
| Bundled upstream data or models slip into a build | `check_shell.py` fails the build on any emitted file not in the cleared list |
| The sandbox cannot judge GPU behaviour | Stated in D2; D3 is yours |
| Upstream evolves while we strip | We pin `f01b6a5`; merging upstream later is a separate decision |
| Two frontends coexist for a while | `apps/web` is untouched until M6; the shell talks to no backend in M5 |
| Node 26 vs upstream's engines field | This machine satisfies it; recorded in `UPSTREAM.md` |

## Effort and order

Phase A is one sitting. Phase B is the bulk (16 steps, most mechanical). Phase C is small but is where the Nexus decisions live. Phase D needs you. I would do A and the first few B steps, show you the first screenshots, and continue once the look is confirmed to survive the strip.

## Self-review

- **Roadmap M5 coverage:** fork and strip in small tested steps (A, B), dark theme and globe behind (kept from the reference), static corner readouts (C4), action-verb skeleton (C2), 2D fallback (C6), basic share links (C5), oil stops only as fixture data (C3). Exit [T]: smoke after each step (A4, B), one Cesium engine (D1), bundle matches the cleared list (D1). [A]: D2. [U]: D3.
- **Placeholders:** the strip steps name what leaves rather than the exact files, because the file list is produced by the dead-import checker at each step; that is deliberate. Interfaces for the Nexus code are in `docs/ui-flows.md` section 7.
- **Unverified:** that the stripped shell keeps the look (checked by screenshots, not assumed); how much of the 250 KB of CSS survives B15; whether every upstream test for a retained module passes on Windows (measured in A3).
