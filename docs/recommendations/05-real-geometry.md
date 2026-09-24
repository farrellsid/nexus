# E. Real geometry and shipping

## Recommendation

Adopt the highway idea as an explicitly modelled maritime network, not as a map of proven cargo movements.
Use sourced network geometry; keep density rasters, computed paths and observed tracks as distinct layers.
Begin with a small reviewed corridor subset and unsmoothed polylines.
Do not invent coastal on-ramps: unresolved port-to-network connections stay absent.
Keep Suez canal, SUMED pipeline and the Cape alternative as separate modal paths.
Use versioned GeoJSON objects plus PostgreSQL metadata initially; PostGIS is optional later.

### Retrieved candidates

Documentation retrieval, not integration validation. URLs below were fetched for this review; file-level licence and geometry checks still gate import.

| Candidate | Verified coverage/resolution/vintage | Licence / cadence / recommendation |
|---|---|---|
| [Eurostat SeaRoute](https://github.com/eurostat/searoute) | Worldwide maritime graph derived from ORNL's 2000 shipping network with European AIS additions; generalized networks at 5/10/20/50/100 km; passage exclusions including Suez and Bab el-Mandeb | [Code EUPL-1.2](https://raw.githubusercontent.com/eurostat/searoute/master/LICENSE). Dataset redistribution chain **UNVERIFIED**, especially original ORNL artefact. No guaranteed data refresh cadence found. Candidate reference graph, not current observed lanes |
| [searoute-py](https://github.com/genthalili/searoute-py) | Python route computation, GeoJSON output, configurable networks/ports/passages; explicitly for visualization, not navigation | [Code Apache-2.0](https://raw.githubusercontent.com/genthalili/searoute-py/main/LICENCE.txt). Bundled network/port provenance and fixed spatial accuracy **UNVERIFIED**. No guaranteed update cadence found. Best bounded Python feasibility candidate once asset rights are settled |
| [World Bank shipping density](https://datacatalog.worldbank.org/search/dataset/0037580/global-shipping-traffic-density) | Global AIS position density, Jan 2015–Feb 2021; 0.005° cells, about 500 m at equator; both moving and stationary positions | Provider declares CC BY 4.0; static historical release, not a live feed. Useful background raster; not a directed graph. “Oil & Gas” class means rigs/platforms/FPSOs, not tanker oil-flow volumes |
| [Marine Regions IHO sea areas](https://www.marineregions.org/downloads.php) | Global sea-area polygons; version 3 dated 2018. Not proof every desired strait has a sufficiently detailed polygon | [Current general terms](https://www.marineregions.org/disclaimer.php) state CC-BY and educational/research scope, with licence terms prevailing. Exact 2018 product licence/scale **UNVERIFIED**; no regular cadence found. Inspect product metadata before reuse |
| [Natural Earth physical labels](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-physical-labels/) | Global small-scale physical-region/marine polygons at 1:10 million; “10m” is scale, not ten-metre accuracy | [Public domain](https://www.naturalearthdata.com/about/terms-of-use/). Release-based, no freshness SLA found. Good globe context; unsuitable to certify port/strait clearance |

SeaRoute's generalization resolution is not a positional-error guarantee. Network nodes/edges from old data do not establish shipping restrictions today. No candidate above is verified as a globally complete, current, freely redistributable operational routing network. A recent library commit would not resolve those questions.

### Network and evidence model

`geometry_version(id, feature_id, source_version_id, asset_hash, geometry_type, crs, bbox, precision_description, valid_period?, recorded_at, derivation_json, rights_id, review_state)`; `network_release(id, geometry_version_ids, topology_hash, source_release_ids)`.

`network_node(id, network_release_id, kind=port|junction|passage_entry|passage_exit, entity_id?, point_geometry_version_id)`; `network_edge(id, from_node, to_node, geometry_version_id, mode=sea|canal|pipeline, directed, passage_id?, length_basis, restrictions_ref?)`.

Treat chokepoints as passage features attached to entry/exit nodes and one or more edges; a centroid alone is insufficient. Port IDs and entrance geometries come from a verified source; no port master list was verified here. Country import totals do not authorize choosing an arbitrary port.

`route_derivation(id, network_release_id, origin_node, destination_node, excluded_passages, cost_rule_version, ordered_edge_ids, derived_geometry_hash, classification=modelled_alternative, created_at)`. Default cost is sourced/geometrically derived length; unknown draught, congestion or closure constraints remain unknown. A user exclusion such as avoiding Suez is a scenario parameter, not an assertion that Suez was closed.

Suez and Cape paths are different graph-edge sequences: recompute with Suez excluded and require the Cape passage/topology for the Cape scenario. SUMED is a pipeline transfer path, never silently traversed as a vessel edge. If graph coverage cannot produce a valid alternative, return unavailable. Store aggregate measurements through `flow_attachment(measurement_version_id, passage_or_segment_id, spatial_basis, direction?, period_id)` only to the extent the source supports that attachment. An aggregate Hormuz value cannot be spread over every inferred downstream branch.

OD lines are allowed as **reported OD relationships** if endpoints and relationship are sourced, visibly distinguished from physical route geometry. A computed route between those endpoints additionally says “modelled connection; path not observed.” A documented actual route requires route evidence; a vessel track requires track evidence. The current oil pack authorizes none of those shipment-specific claims. Require all three distinctions in the legend, tooltip and exported image.

### Smoothing and area geometry

Preserve original vertices. First use renderer antialiasing and view-level simplification with a disclosed tolerance; do not change factual geometry to make it prettier. Later, constrained corner rounding can derive a display-only curve inside a verified water/corridor mask: lock ports and passage endpoints, bound deviation from the original line, densify the candidate curve and test every segment against land and excluded passages. Reject smoothing when any check fails; fall back to the source line. An unconstrained spline can overshoot land even when its control points are in water.

A calculated intermediate vertex is permissible only as a labelled, reproducible geometric derivative, never a newly “sourced waypoint.” Under a strict interpretation forbidding such derivatives, skip smoothing entirely. Nearest-node port snapping is especially dangerous: searoute-py documents moving land points to nearby sea points. Disable or disclose/review that operation; it is not verified port access.

Use `Polygon`/`MultiPolygon` for straits and regions, with holes, closed rings, provider feature IDs and boundary interpretation. Keep label anchors separate. The local God's Eye Natural Earth derivative drops holes, small parts and two sliver-only marine features, rounds coordinates and stores open rings (`src/data/local_data/natural_earth/README.md`): it is display data, not a water-clearance mask. Do not turn its label extents into authoritative strait limits.

Storage proposal: immutable GeoJSON in a content-addressed directory, PostgreSQL rows for IDs/provenance/versions/topology, and compact reviewed assets in static exports. Explicitly use longitude/latitude at the boundary and validate coordinate ranges, finite values, topology and antimeridian splitting. Add PostGIS only when measured spatial queries justify the install/distribution burden. Do not imply PostGIS is needed merely to draw polygons.

## Evidence from the repo

`geography.py` currently validates route point count but not geographic ranges, land crossings or polygon validity. `investigation.py` validates IDs/endpoints. Oil geography contains six stops and two remaining routes (O-R01 Suez/SUMED, O-R03 Myanmar–China), both endpoint lines; no Cape route or polygons. `seed_payload()` excludes geography from review storage. Inspected `.local/postgres-runtime/pgsql/share/extension/*.control`: pg_trgm, unaccent and fuzzystrmatch present; no vector/postgis control files. This is a filesystem observation, not an installed-extension query.

The development-status explanation overgeneralizes the failed Cape attempt: land crossings were a failure of those selected anchor chains, not an inherent inability of polylines to approximate a curved maritime path. A sufficiently detailed sourced route geometry can be a polyline. Real headland coordinates alone do not establish the intervening offshore route.

## Options considered

| Option | Assessment |
|---|---|
| Smooth lines between sourced endpoints | Reject as real routes; still can cross land and invent path knowledge |
| Build a global AIS-derived graph now | Excessive acquisition/rights/coverage work for the current corpus |
| Small sourced graph + labelled computed alternatives | Recommended feasibility step; licence-gated |
| Historical density background only | Honest low-risk fallback while graph rights remain unresolved |

## Migration and compatibility impact

Keep 44 claim histories intact; geometry gets its own append-only review/version lineage and source references. Old geography is retained as a legacy release, not silently replaced or promoted. The additive claim generator intentionally does not manage geography; add a separate reviewed import and ensure exports pin both evidence and geometry release IDs. No history triggers disabled. Retain existing stop/entity aliases and old route IDs for citation resolution. Tests before promotion: Cape/Suez distinction, separate SUMED mode, no false OD inferred from aggregates, port snapping failure, antimeridian, smoothing land intersection, and visual inspection in both globe and fallback.

## Risks

Visually plausible paths can be epistemically false. Old network data may omit channels or restrictions. Schematic widths can look like physical lane boundaries. Coarse land masks cannot validate narrow canals. Global density rasters are large relative to the current corpus and should not enter a default pack wholesale.

## Effort

**L** for globally credible routing; **M** for a small reviewed geometry pilot. A/B/D define identity, period and flows; J rights clearance is a prerequisite to distribution; F consumes pinned geometry.

## Decisions needed from the user

Approve labelled modelled alternatives alongside sourced aggregate chokepoint flows, starting with a small corridor subset and no automatic port on-ramps?

## Unverified or not checked

No network downloaded, package installed, route calculated or topology tested. Original ORNL/network/port rights, exact maritime polygon coverage, operational restrictions and provider update guarantees remain **UNVERIFIED**. No asserted “IHO publishes every strait boundary” shortcut is justified by the retrieved pages.
