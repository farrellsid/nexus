# Nexus shell

The visual shell for Nexus: a Cesium globe in a dark console look, a scene director that plays guided camera tours, and the current oil-system anchors as its only data. It is built on [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) by Bilawal Sidhu, a stripped fork used under its MIT licence. The look, layout, effects and much of the interface code are his work; Nexus keeps them and replaces the data and the purpose. [UPSTREAM.md](UPSTREAM.md) records what was imported, what was removed and how each step was checked; [LICENSE](LICENSE) is the upstream licence.

This is a prototype of the look and the interaction model (roadmap M5). It is not the analysis workbench, which lives in `apps/web`, and it shows nothing that is not sourced in `investigations/`.

## What is in it

- The globe, camera, hover, HUD, command dock, celestial ring, split-flap readouts, logo and Data Layers / Scenes / Display panels.
- Two keyless imagery stacks (Esri Satellite, OpenStreetMap) over Re:Earth terrain. By default the page contacts only `127.0.0.1`, `services.arcgisonline.com` and `terrain.reearth.land`; choosing the OSM stack adds `tile.openstreetmap.org`.
- Two Nexus layers, `nexus-oil-stops` (six sourced anchors) and `nexus-oil-corridors` (two sourced lines), and one guided tour over the stops. Each anchor carries its precision, caveat and source.

Everything else upstream shipped (live aircraft, ships, satellites, cameras, voice, geocoding, key set-up, datasets) is removed.

## Run it

```
npm ci
npm run dev        # http://127.0.0.1:4173
npm run build
```

Node 24.14+ or 26 is required (`package.json` `engines`).

## Where things are

| Path | Purpose |
|---|---|
| `src/nexus/` | New TypeScript: the oil layers, the tour, and the generated `oilStops.ts` |
| `src/app/`, `src/ui/` | Scene construction, panels and the shell's controllers (upstream, trimmed) |
| `src/data/` | The layer manager, layer-state registry and share tokens |
| `src/scenes/` | The scene director and recipes |
| `src/maps/` | The two imagery stacks and the terrain factory |
| `scripts/` | Checks: formatting, package boundaries, dead modules, one Cesium engine, generated-file drift |
| `tests/` | The Playwright smoke test and its allowed hosts and known errors |

`src/nexus/oilStops.ts` is generated from `investigations/02-oil-system/geography.json` and the evidence pack by `scripts/generate-oil-stops.mjs`; do not edit it by hand. `npm run check:generated` fails when it drifts.

## Checks

```
npm run typecheck          # tsc, strict, new code only
npm test                   # unit tests, JavaScript and TypeScript
npm run check:generated    # oilStops.ts matches its source
npm run check:boundaries   # import directions and package boundaries
npm run check:dead         # dangling imports and unreachable modules against the recorded baseline
npm run check:engine       # exactly one @cesium/engine
npm run build
npm run e2e               # smoke: the shell renders quietly and the oil layers add and remove entities
```

New code is TypeScript; the inherited JavaScript stays JavaScript.
