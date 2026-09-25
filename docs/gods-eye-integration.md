# God's Eye View integration trial

Checked 2026-09-22 against `bilawalsidhu/gods-eye-view` main. Nexus uses a narrow, adapted part of its MIT-licensed map approach rather than forking the whole application.

## Reused now

- Cesium as the browser globe renderer.
- A caller-owned viewer with most stock controls disabled so the existing Nexus workbench remains the application shell.
- A keyless Esri World Imagery source with OpenStreetMap fallback.
- Provider credits rendered next to the globe.
- Camera movement from selected, sourced longitude/latitude anchors.
- Automatic fallback to a bundled Natural Earth world map when the browser has no usable WebGL texture capacity or Cesium reports a rendering error.

The adapted implementation is `apps/web/src/workbench/CesiumGeographyMap.tsx`. The original source is <https://github.com/bilawalsidhu/gods-eye-view>; its MIT notice is retained in `THIRD_PARTY_NOTICES.md`.

## Deliberately excluded

- Live aircraft, vessel, satellite, camera and other tracking feeds.
- God's Eye View's HUD, voice controls, scene director and source-specific panels.
- Google Photorealistic 3D Tiles and Cesium ion services, which require separate credentials and provider terms.
- Bundled third-party datasets and 3D models whose licences differ from the repository's MIT code licence.

Nexus remains responsible for entity IDs, evidence, review state and geographic precision. A map marker remains a sourced label anchor; it is not a facility boundary, shipping track, pipeline route or cargo position. Map-source failures cannot mutate evidence records.

## Later candidates

- Extract the tested map-stack controller if Nexus adds user-selectable imagery or terrain.
- Add sourced GeoJSON route and area layers through a separate geography review contract.
- Evaluate optional photorealistic 3D only after credentials, costs, terms and a clear product need are agreed.

## User decision, 2026-09-22: the visual base should come from God's Eye View, not be rebuilt

The user reviewed the current oil geography view and judged it a generic, from-scratch look rather than the God's Eye View identity they want Nexus built on. `CesiumGeographyMap.tsx` currently reuses only the Cesium/imagery-provider mechanics; its dark tactical-HUD design system — `foundation.css`, `cockpit.css`, `command-dock*.css`, `overlays.css`, and the JS-driven chrome in `hud.js`, `splitFlap.js`, `scopeMask.js`, `panelStackLayout.js` (see the local clone at `.local/references/gods-eye-view`) — was excluded, not adapted. The user's direction: when visual work on the geography view resumes, the base look and feel should be pulled from that design system and pared down to what Nexus needs, not reinvented. This is a decision to act on when visual work is actually scheduled — not authorization to restructure the geography layer now. Current milestones (`docs/development-status.md` "Next increments") are route/area geometry and the geographic review model, not the visual base.

## 2026-09-25: the shell is built (`apps/shell`)

The user's 2026-09-22 decision was carried out as milestone M5: a stripped fork of God's Eye View at `f01b6a5`, in `apps/shell`, rather than the narrow adaptation in `apps/web`. `apps/shell/UPSTREAM.md` lists what was imported, every removal and every change; `apps/shell/README.md` says how to run and check it.

- **Kept:** the globe, scope mask, HUD, command dock, celestial ring, split-flap readouts, scene director, and the Data Layers, Scenes and Display panels, with their stylesheets (pruned from 261 KB to 89 KB).
- **Removed:** every live layer (aircraft, vessels, satellites, cameras, quakes, fires, traffic, transit, radio, cables), voice, geocoding and place services, annotations, the key-setup wizard, Google 3D Tiles, Bing and Cesium ion, all bundled datasets and models, and upstream's documentation.
- **Changed by the assistant (proposals, not user decisions):** the name, logo and icons are Nexus's own; the HUD shows only camera-derived values and says "not a live feed" instead of classification banners and invented mission, sensor and orbit ids; the shell opens on the Indian Ocean; the location presets are the oil stops; the share-link parser range-checks its input.
- **Added:** `src/nexus/` in strict TypeScript (oil layers, tour, readouts, action layer, global context, fallback map), a generated `oilStops.ts` that cannot drift from `geography.json`, and the checks named in `apps/shell/README.md`.

The rules above still hold: a marker is a sourced label anchor, never a route or a position, and no map or shell failure can change evidence.
