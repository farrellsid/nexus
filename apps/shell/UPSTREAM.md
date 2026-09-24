# Upstream and strip log

This folder is a stripped fork of **God's Eye View** by Bilawal Sidhu, <https://github.com/bilawalsidhu/gods-eye-view>, imported at commit **`f01b6a5`** ("fix(ui): stop panel glows from adding scrollbars to the narrow-screen rails (#699)"). Its MIT licence is in `LICENSE`. The MIT grant covers the source code only; upstream states that its third-party data and assets are excluded. See `THIRD_PARTY_NOTICES.md` at the repository root.

Plan: `docs/superpowers/plans/2026-09-24-m5-visual-shell.md`. Branch: `m5-shell`. Each step below is one commit.

## What was left out of the import (deviations from "unmodified")

- `.git`, `node_modules`: not source. (`build/` is source here, not output: `build/application-html.js` is imported by tests, and my first import wrongly excluded it. Restored in A1b.)
- `docs/media/` (about 69 MB of demonstration GIFs) and `.github/` are not imported. Upstream's `docs/*.md` (512 KB) are imported, because 23 test files assert documentation consistency.
- `src/data/`, `public/models/`, `public/events/` are **on disk but ignored by git** (`.gitignore` here). They are upstream's bundled datasets, 3D models and event media, whose licences are not cleared for this repository. The app still needs them to start until the strip steps that own them remove the code that reads them; each such step deletes its files. They never enter git history.

## Step log

| Step | What changed | Tests | Smoke | Notes |
|---|---|---|---|---|
| A1 | Imported the reference code unmodified (apart from the exclusions above) | not yet run | not yet run | 961 tracked files |
| A1b | Restored `build/` and imported `docs/*.md` after a first run showed 23 failing test files caused by my exclusions | 4168 tests, 4158 pass, 0 fail, 10 skipped: identical to the untouched clone | not yet run | the mistake and its fix are recorded rather than hidden |
| A2 | `npm ci` (PUPPETEER_SKIP_DOWNLOAD=1) and first run | as A1b | renders | 15 s install; upstream's lockfile already resolves **one** `@cesium/engine` (22.3.0, `@cesium/widgets` 14.3.0 deduped) |
| A3 | Baseline measurements | as A1b | | `vite build`: 423 files, 31.2 MB in `dist/` (Cesium.js 5.6 MB, egm96 2.7 MB, datacenters.geojsonl 2.5 MB, regions 1.9 MB); `check:boundaries` passes |
| A4 | Added the step checks: Playwright smoke (`tests/smoke.spec.mjs`, `known-errors.json`), `scripts/nexus-dead-modules.mjs` (baseline: 1147 modules, 328 tests, 681 reachable; 2 dangling and 40 unreachable recorded as the allowed list), `scripts/nexus-check-engine.mjs`, and `npm run check:step` | as A1b | 0 console errors; screenshot 755 KB (`.local/m5/a4-baseline.png`) | external hosts at load: `fonts.googleapis.com`, `fonts.gstatic.com`, `services.arcgisonline.com`, `terrain.reearth.land` |

## How a step is checked

`npm run check:step` runs, in order: the upstream unit tests, the dead-module checker (`--strict`, so it fails on any new dangling import or unreachable module, and on a stale allowed-list entry), the one-engine check, and the Playwright smoke test (renders, and no console error outside `tests/known-errors.json`, which can only shrink). The sandbox GPU is not the user's: a green smoke test means "renders and is quiet", not "looks and performs right". The 40 unreachable modules on the baseline are loaded through computed dynamic imports that a static scan cannot follow; each strip step deletes the ones it owns and removes them from the list.
