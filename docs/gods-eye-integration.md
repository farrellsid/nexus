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
