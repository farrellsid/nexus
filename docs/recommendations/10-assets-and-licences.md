# J. Assets and licences

## Recommendation

Reuse a narrowly inventoried visual foundation; do not copy the entire reference public/data directories.
Recommend MIT for Nexus-authored code and CC BY 4.0 for Nexus-authored documentation/curation, with explicit third-party exclusions.
Keep per-component rights; a pack's single licence label cannot relicense its source material.
Self-host pinned fonts/icons with their notices; replace unverified loose SVG assets.
Block release of unverified assets and excerpts, rather than assuming public accessibility grants reuse rights.

### Reuse inventory and verification

Inspected reference checkout `f01b6a5d8462c182e03c94493fa24098c1ac3771` (`git -C .local/references/gods-eye-view rev-parse HEAD`). Paths below are relative to that checkout. “Verified” means a specified licence document was read; it does not mean all upstream authorship or every derived byte was independently audited. The accompanying `repo-audit.json` enumerates files/hashes and package notice entries. This is a source-tree audit; a final rebuilt bundle does not yet exist.

| Asset / exact family | Intended disposition | Licence evidence / status |
|---|---|---|
| `style.css`; `src/ui/styles/foundation.css`, `cockpit.css`, `command-dock.css`, `command-dock-compact.css`, `command-dock-trays.css`, `command-dock-sliding.css` | Adapt selected styles | Source code MIT, local `LICENSE` and [upstream licence](https://github.com/bilawalsidhu/gods-eye-view/blob/main/LICENSE) read; retain copyright and modification notice |
| `src/ui/styles/controls.css`, `location.css`, `status.css`, `overlays.css`, `scenes.css`, `responsive.css`, `first-run.css`, `provider-settings.css` | Adapt only required components | Same MIT source grant; no separate stylesheet asset licence found |
| `layers.css`, `radio.css`, `cctv.css`, `bhote-koshi.css`, `recording.css`, `voice-cost.css` | Exclude feature-specific rules unless individually justified | MIT code, but copying their linked data/media is a separate rights question |
| Viewer/map controllers, `splitFlap.js`, `celestialRing.js`, camera/director/share/onboarding code, action schema, shader source | Adapt behavior/presentation | MIT source grant; isolate imports from default scenes, live feeds and event datasets |
| Inter font, remotely linked in `index.html` | Keep as pinned self-hosted font | [Author licence](https://raw.githubusercontent.com/rsms/inter/master/LICENSE.txt): SIL OFL 1.1, verified; include font licence, preserve applicable naming conditions |
| JetBrains Mono font, same HTML | Keep as pinned self-hosted font | [Author licence](https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/OFL.txt): SIL OFL 1.1, verified |
| Material Symbols Outlined, icon-name subset in `index.html`; foundation `.material-symbols-outlined` | Keep only needed icons/font subset | [Google guide](https://developers.google.com/fonts/docs/material_symbols): Apache-2.0, verified; retain notice and exact asset version |
| SF Mono, Fira Code, `-apple-system`, BlinkMacSystemFont fallback names | Do not bundle font binaries based on these declarations | CSS only refers to installed/system fonts. Redistribution licences for hypothetical binaries **UNVERIFIED**, not required if not distributed |
| `public/location.svg`, `public/visual-presets.svg` | Referenced by command-dock CSS; replace with verified icons | No individual authorship/licence metadata in files; MIT covers source code but explicit third-party asset carve-out prevents assuming these are cleared. **UNVERIFIED** |
| `public/pin.svg` | Referenced by command-dock template; replace | **UNVERIFIED** individual asset provenance |
| `public/logo.svg` | Loading/HUD references exist; use Nexus identity instead | **UNVERIFIED** artwork/trademark rights; code MIT is insufficient brand clearance |
| `public/mic.svg` | Exclude with voice | **UNVERIFIED** individual provenance |
| Cesium runtime including widget CSS, images, sky/texture assets, workers/codecs | Keep only distribution required by the selected package | [Cesium licence](https://github.com/CesiumGS/cesium/blob/main/LICENSE.md) and installed `node_modules/cesium/LICENSE.md`: Apache-2.0; preserve installed `ThirdParty.json` and notices. Individual transitive assets not independently cleared; do not strip notices |
| `src/data/local_data/natural_earth/{regions,marine}.json` | Optional region display; not routing mask | [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/): public domain verified. Local README records derived geometry transformations, source commit and exclusions. Exact regeneration not verified |
| Esri World Imagery runtime service | Optional, public use blocked pending terms check | Provider-specific service/content terms, **UNVERIFIED** entitlement for exact keyless endpoint; retain provider-generated attribution if approved (G) |
| OSM standard runtime tiles | Optional under service policy | [OSM data](https://www.openstreetmap.org/copyright): ODbL; [tile service policy](https://operations.osmfoundation.org/policies/tiles/) separately applies. Data licence is not unlimited tile hosting |
| Re:Earth terrain URL in `src/maps/terrain.js` | Exclude initially; ellipsoid fallback | Code comment claims CC BY 4.0. [Mapterhorn](https://mapterhorn.com/) instead points to source-specific terrain licences. Exact Re:Earth dataset/service terms **UNVERIFIED**; do not repeat comment as blanket clearance |
| Cesium ion/Google imagery, terrain and Places | Exclude paid/keyed integrations | Account/service terms not audited for Nexus; not covered by code licence |

No standalone raster artwork was found in the retained core CSS URLs; the identified CSS asset links are the two SVG masks. The full file inventory additionally covers assets that must stay excluded. Inline procedural geometry/shader effects are source code; a coordinate dataset embedded in JavaScript remains data, regardless of extension.

### Bundled material that must not enter the foundation by accident

| Files/family found locally | Existing local notice | Verification and disposition |
|---|---|---|
| `local_data/telegeography_submarine_cables/{cable-geo,landing-point-geo,source}.json` | CC BY-NC-SA 3.0 in LICENSE/DATA_SOURCES | Provider terms not independently fetched here: **UNVERIFIED** for redistribution; exclude |
| `local_data/datacenters/datacenters.geojsonl`; `dams/dams.geojson`, `dams.geojsonl` | OSM/OIM ODbL 1.0 | OSM licence fetched; extract provenance/derivation compliance not independently audited; exclude |
| `local_data/neighborhoods/san-francisco.json` | DataSF PDDL 1.0 in `SOURCE.md`/DATA_SOURCES | Provider metadata not fetched: **UNVERIFIED**; no need in industry foundation |
| `local_data/cctv_ground_heights/cctv_ground_heights.json` | Local derivation README | Provider/derived-height rights **UNVERIFIED**; exclude CCTV |
| `public/events/bhote-koshi-2026/{pre,post}.webp`, `event.json`; `src/data/bhoteKoshiFloodPath.js` coordinates | Vantor/GeoPera CC BY-NC 4.0 in LICENSE | Original source not fetched: **UNVERIFIED**; exclude event imagery AND derived coordinates |
| `public/models/{airplane,atr72,b789,bell206,c172,citation2,jet,mq9,ship}.glb` | Nine per-model CC BY 4.0 notices in `public/models/README.md` | Original model pages not fetched: **UNVERIFIED** individually; exclude all nine |
| `src/layers/alpr/assets/alpr-marker-{normal,selected,selected-brackets}.png` | No individual notice established | **UNVERIFIED**; exclude ALPR assets |
| `docs/media/{youtube-popular-videos,open-source-survey}.png` | No individual notice established | **UNVERIFIED**; documentation screenshots excluded from app reuse |
| FIRMS snapshot mentioned by upstream docs | CC0/public-domain claim in upstream notice | No matching standalone local_data file in directory enumeration; **UNVERIFIED** asset presence elsewhere; exclude fire integration |

### Pack/code licensing policy and build check

[MIT](https://opensource.org/license/mit) is a simple proposed code choice compatible with preserving the upstream MIT notice; this review does not license the user's code on their behalf. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) is proposed for original Nexus explanations and curation to require attribution. Keep original public-domain and separately licensed components identified. Do not put a blanket CC BY label on copyrighted excerpts or third-party databases.

Correct `data-packs.md`'s “most restrictive source” simplification: linking to a restrictive source does not automatically apply its licence to the entire original pack, and incompatible components cannot be legalized by selecting the most restrictive label. Track what is actually redistributed or derived, under what permission, and keep components separable. Legal treatment of a particular excerpt/database remains a specific rights decision, not an automated conclusion.

Proposed manifest component record: `path_or_record_id`, `sha256`, `origin_url`, `origin_version`, `creator`, `licence_expression_or_LicenseRef`, `licence_evidence_url`, `licence_checked_at`, `attribution_text`, `modification_notice`, `redistribution=allowed|reference_only|local_only|blocked|unverified`, `permission_basis`, `reviewer`. Distinguish source-link-only records, factual data, excerpts, authored prose, third-party geometry and software. A source URL alone does not authorize excerpt republication.

Build gate: enumerate **emitted files**, static assets copied by build plugins, runtime external requests and pack components; require manifest coverage; reject blocked/unverified included content; check allowed use/distribution against reviewed policy; generate notices and visible map credits; assert excluded models/event data do not ship; scan for secrets/private snapshots; cap archives and forbid executable payloads. Keep licence text and notice artefacts with packages. Use registry allowlists plus human review for custom/ambiguous licences, not a simplistic SPDX-string sort. Compare dependency trees for duplicate Cesium engines as a separate runtime gate.

## Evidence from the repo

Read root/reference LICENSE/notices, reference `index.html`, stylesheet imports/URLs, local-data READMEs, model README, `src/maps/{imagery,terrain}.js`, and installed Cesium LICENSE/ThirdParty.json. Enumerated public/local_data/assets and styles. `repo-audit.py` reproduces the file inventory and pack counts without modifying the repository. Root Nexus has `THIRD_PARTY_NOTICES.md` but no LICENSE file. Oil rights fields flag O-S03/O-S06/O-S19/O-S20; absence of a flag on copper is not clearance.

## Options considered

| Option | Assessment |
|---|---|
| Reuse the whole fork under MIT | Reject: upstream expressly excludes third-party data/assets |
| Exclude every upstream component | Unnecessary; source styles and verified fonts/icons can be reused |
| Narrow asset manifest and fail-closed public export | Recommended; resolves actual intended reuse without an exhaustive unrelated feed audit |

## Migration and compatibility impact

Add rights assessments/version records rather than edit the 34 old source records or 44 immutable claims. Public export eligibility is a separate policy, not retroactive rejection of accepted facts. The additive generator cannot update rights-only metadata safely; use dedicated append-only rights tables/new release manifests. Preserve raw review history when an excerpt is withheld from a distributable pack; link its source and record the reason. No licence files or notices outside recommendations were changed.

## Risks

“Short excerpt,” “open source” and “keyless” are not licence permissions. Source code can contain data. A copied runtime directory can ship unused restricted assets even when no code imports them. Public-domain geometry can still be too simplified for the analytical purpose.

## Effort

**M** for retained foundation/build manifest; **L** for every source/excluded provider. Gates E/G distribution and the visual rebuild; I uses the rights policy.

## Decisions needed from the user

Choose MIT for original code and CC BY 4.0 for original documentation/curation, preserving separate third-party rights? Exclude non-commercial and unverified assets from the default distributable release?

## Unverified or not checked

This is not a final legal clearance or complete transitive package audit. Loose SVG origin, exact Esri/Re:Earth use terms, excluded dataset/model provider permissions, copper excerpts, and the final emitted bundle remain **UNVERIFIED**. No asset was downloaded/copied into Nexus and no licence selected on the user's behalf.
