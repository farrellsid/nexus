# Frontend rebuild on a God's Eye View foundation

Design record for the 2026-09-22 decision to rebuild Nexus's frontend starting from `bilawalsidhu/gods-eye-view`'s visual/interaction foundation, rather than continuing to adapt isolated pieces into the existing React app. This supersedes the "narrow adapted seam, not a fork" approach recorded in `docs/gods-eye-integration.md`'s original sections; that document's licensing/attribution material and the specific reuse/exclusion list from the first integration attempt remain accurate background.

Status: architecture decided by the user; phase 1 not yet planned or implemented. This is a design record, not authorization to deploy, incur costs, or add a model provider.

## Why

The user judged the current from-scratch Cesium wrapper (`apps/web/src/workbench/CesiumGeographyMap.tsx`) a generic, thin reimplementation lacking the actual God's Eye View look and interaction quality (hover, camera work, HUD chrome). A long investigation (see `docs/development-log.md`, 2026-09-22 entries) found and fixed the specific bug that had been blocking the globe from rendering at all (a duplicate `@cesium/engine` dependency) — but the user confirmed the rebuild decision stands independent of that fix: **this is about visuals and interaction quality, not just getting Cesium to render.**

## Decided: what survives from each side

**Backend — kept, evolves.** Python/FastAPI + PostgreSQL, chosen on the merits even disregarding the existing working implementation: PostgreSQL for recursive-CTE graph traversal, `tsvector`/`pgvector` for text and future embedding search, JSONB for evidence payloads, real transactional guarantees for append-only review. Python for where the project's hard problems actually are — multilingual source discovery, PDF parsing, entity resolution, embeddings, future LLM orchestration — and because Pydantic's runtime validation at boundaries matters unusually much for a project whose entire value is not corrupting provenance. God's Eye's own `server/` is a thin proxy for live third-party feeds (flights, vessels, CCTV) — orthogonal to what Nexus's backend does; nothing there to adopt.

**Frontend language — TypeScript, not God's Eye's plain JS.** Adopting their visuals does not require adopting their language: their look lives in `foundation.css`, `cockpit.css`, `command-dock*.css` and their layout/interaction design, all of which port to any framework. Their plain-JS hand-rolled DOM manipulation is a constraint of their project, not a feature worth emulating. Discriminated unions catch exactly the bugs this project can't afford: mixing up observation vs. inference vs. forecast, mis-binding a claim to the wrong entity, rendering an unresolved coordinate as if known.

**From God's Eye — keep and adapt:**
- Cesium globe: camera controls, click/hover-to-focus, keyless Esri imagery + OSM fallback (already working via the dependency fix)
- HUD-style visual chrome: split-flap readouts, celestial ring, tactical typography/panel layout, bloom/GLSL "sensor look" post-processing
- Scene director / cinematic camera tours — repurposed for Nexus's existing guided-geography stops
- Share links (camera + selection + state → URL) — Nexus doesn't have this today
- "Global Context" pattern (stage a full view, restore prior state on exit)
- First-run onboarding and loading-state UX patterns
- The *shape* of their voice action schema (`src/voice/actionSchemas.js` — JSON-schema tool-call definitions like `fly_to_location`) as the model for Nexus's action-layer API (see below), without building voice itself

**From God's Eye — strip:**
- All live tracking layers and their data plumbing: flights, military flights, AIS vessels, CCTV, ALPR, radio, traffic, bikeshare, military installations, satellites, rocket launches, FIRMS fire heatmap, the "Contacts" roster, detection overlay, 3D aircraft hangar
- Voice control (needs an OpenAI key; out of scope, see "chat later" below)
- Google Maps/Places integration (needs a paid key; Nexus's entities are a closed curated set with known coordinates, so the geocoding-anywhere-on-Earth problem mostly doesn't apply)
- Pinokio installer/updater plumbing (irrelevant to a dev-only local tool)
- Most of the "POWER UP" key-setup panel, though its pattern of graceful degradation with zero keys configured is worth keeping — Nexus already works this way

**Explicitly deferred, not designed here:** the AI chat agent itself. No model provider is chosen and AGENTS.md is explicit nothing in this project is authorized to incur model costs. What *is* in scope now is designing the action-layer API (below) so the chat agent has a clean integration point later, since retrofitting it after hover/tours are hardwired to internal state would be expensive and designing for it now is cheap.

## Decided: data model changes

**Container model — industry as domain, investigations inside it.** Today `case_id` conflates industry + time window + question (`oil-system-2025q3-2026q2`, `kamoa-to-cables`). Going forward: an industry (`oil`, `copper`) is a persistent domain; investigations are bounded briefs/time-slices/questions within it. Entities are owned by the industry and reused across its investigations rather than duplicated per-brief.

**Shared entity registry across industries.** Entities live once, globally; industries are views/tags over them. Checked against current data: the oil and copper packs have **zero entity name overlap today** (verified 2026-09-22), so this migration is cheap now and gets expensive to do later once both industries independently model shared things like China, shipping lanes, or ports. Both packs need re-IDing regardless — oil uses `oil-`-prefixed ids (`oil-china`, `oil-hormuz`) that are wrong for a shared registry, copper uses bare ids (`smelter`, `cathodes`) that are ambiguous at global scope.

**Entity type taxonomy — two-level category + subtype.** Broad `category` drives the default UI display template; precise `subtype` refines it, mapped to a published external vocabulary where one actually fits and left explicitly bespoke where none does. Oil's 11 types and copper's 7 overlap on only 3 and must be reconciled into one vocabulary.

Prior-art research (2026-09-22, background agent; full findings archived in the agent transcript, key points below) found **no existing project doing what Nexus does end-to-end** — closest analogs are Trase.earth (provenance-conscious material-flow mapping, but scoped to agricultural commodities and input-output modelling, not an infrastructure/company entity registry) and an arXiv paper, *"An Evidence-First Multi-LLM Framework for Auditable Critical-Infrastructure Dependency Modeling"* (https://arxiv.org/html/2609.12360), whose four-way match-confidence scheme — Direct-Equivalent / Safe-Superclass / Related-Only / Unmapped — is worth adopting as the confidence label on each subtype's external mapping below, since it's methodologically the closest published pattern for exactly this problem even though it's a different domain (critical-infrastructure security, not commodities) and uses a coarser evidence classification than Nexus's own observation/claim/inference/forecast split.

Recommended taxonomy:

| Category | Example subtypes | External mapping | Confidence |
|---|---|---|---|
| `place` | `country`, `production_region`, `maritime_chokepoint`, `maritime_route`, `port` | Wikidata classes (confirmed: Hormuz P31=strait, Q79883); ports also via UN/LOCODE | Direct-Equivalent |
| `facility` | `mine`, `concentrator`, `smelter`, `refinery`, `export_terminal`, `power_plant` | Bespoke enum, cross-referenced to OSM `industrial=*` and Global Energy Monitor tracker facility types where a GEM tracker exists for the sector | Unmapped, GEM/OSM-referenced |
| `infrastructure` | `pipeline`, `rail_line`, `transmission_line`, `cable_route` | OSM `man_made=pipeline` and equivalents; distinguished from `facility` by geometry (line vs. point), not function | Safe-Superclass |
| `transport_corridor` | `canal_corridor` (Suez/SUMED), `rail_corridor` (Lobito) | Bespoke — no standard treats a mixed pipeline+canal+port corridor as one object; use only where Nexus needs the corridor reasoned about as a single unit | Unmapped |
| `organization` | `company`, `producer_group`, `intergovernmental_organization`, `regulator` | GLEIF ELF/LEI (ISO 20275/17442) where an LEI exists (likely for Trafigura, Aurubis, Prysmian); Wikidata `intergovernmental organization` for bodies like OPEC | Direct-Equivalent where LEI exists, Related-Only otherwise |
| `material` | `crude_oil`, `copper_cathode`, `sulfuric_acid` | HS codes where customs-traded (2709 crude petroleum; 7403.11 copper cathodes) | Direct-Equivalent |
| `industry` | `oil_refining`, `copper_smelting` (an activity, not an asset) | ISIC/NACE activity codes; NAICS 331410 confirmed as the closest US analog for copper smelting/refining | Safe-Superclass |

**Traps this taxonomy is designed around** (from the research; each is a modeling rule, not just a caveat):
- **Process stage vs. physical asset**: "smelter" is both a `facility` subtype and a stage in a material's processing chain. Keep `facility.subtype=smelter` for the asset registry entry; model process stage (ore → concentrate → matte → blister → cathode) as a separate attribute/relationship, not a type — otherwise subtypes multiply combinatorially.
- **Place that is also a constraint**: a strait is unambiguously `place` (confirmed Wikidata P31=strait for Hormuz), but Nexus cares about its throughput capacity. Keep category `place`/subtype `maritime_chokepoint`; attach flow capacity as a fact/claim on the entity, not a second "constraint" category — otherwise every pipeline segment and port berth with a throughput limit double-counts into a parallel taxonomy.
- **Organization that is also a policy actor**: OPEC carries four simultaneous Wikidata types (international organization, advocacy group, intergovernmental organization, cartel — confirmed Q7795). Category stays `organization`; policy-setting is a fact on the entity, not a `policy_actor` category that would overlap `organization`.
- **Material has no coordinates**: crude oil (Wikidata Q22656, confirmed) has zero locational semantics. `material` must be structurally excluded from any UI path that expects a map pin — enforced by the category gating which display template is even offered, not left to per-entity discipline.
- **No governing standard agrees on "facility"**: GEM trackers are per-sector with no unified cross-sector ontology; OSM's own wiki flags `industrial=*` as too vague for this; NAICS/ISIC classify the activity, not the site. `facility` subtypes are necessarily a bespoke, Nexus-curated enum, cross-referenced to GEM/OSM per subtype for groundedness — not claimed to map onto an authoritative standard, because none exists at this granularity.
- **LEI doesn't cover everyone**: OPEC and informal producer alliances have no LEI (it requires being a legal party to a financial transaction). Keep `organization.subtype` bespoke with LEI as an optional cross-reference, never a required identifier.

**Explicitly unverified, do not cite as settled**: Altana, Sourcemap, and Panjiva/S&P publish no public ontology documentation the research agent could locate — nothing about their type systems should be asserted in this project. UN/CEFACT recommendations beyond UN/LOCODE, and ISO 15926/Industrial Ontology Foundry specifics beyond their public scope/abstract pages (the full ISO standard text is paywalled), were not independently verified and should be re-checked before being relied on for anything beyond the general orientation given here.

**Metric → entity linkage — currently missing, required.** Checked against current data: `briefing.metrics` entries carry `source_ids` but no `entity_id` (verified 2026-09-22) — the connection between the "Strait of Hormuz" entity and its `O-M01` flow metric exists only implicitly in a title string. Hover-to-show-metrics has no data backing without adding this link explicitly.

**Significance / level-of-detail — evidence criterion where it exists, curated tier as fallback.** Checked against current data: entities carry no significance/rank field today (verified 2026-09-22), so there's nothing to drive "show the important stuff zoomed out, more detail zoomed in" — the direct answer to the user's crowding concern from experience mapping global trade as a graph. AGENTS.md already states the principle ("detail follows explanatory significance") but nothing implements it, and it explicitly warns against the easy wrong implementation: *"reserve 'critical' or 'bottleneck' for a defined, supported criterion rather than visual prominence or graph degree alone"* — so ranking by claim count or graph degree is ruled out. Each industry should define a sourced significance criterion where the data supports one (e.g. oil: share of global flow; copper: share of refined output), surfaced honestly as "shown because it carries X% of flow, per source Y" — not as an unqualified importance claim. Where no such criterion exists yet (abstract entities, thin early data), a curator-assigned display tier is the fallback, explicitly documented as a reading aid and never presented as a factual claim.

## Decided: the action-layer API

One shared API — not three separate systems — should back mouse interaction, guided tours, and (later) a chat agent: verbs like `select_entity`, `focus_camera`, `show_layer`, `highlight_metric`. Mouse clicks call it directly. Guided tours are a scripted sequence of calls to it. A future chat agent calls the *identical* actions via LLM tool-calling, exactly as God's Eye's voice system already does with its own action schema. This means a future "what's happening at Hormuz" chat query could both answer in text and actually fly the camera there and surface the sourced flow metric — because the chat agent is just another caller of the same surface everything else uses.

Concrete verb list, request/response shapes, and how this maps onto React state are not yet designed — this section records the *principle* (one shared action surface, modeled on the God's Eye tool-call pattern) as decided; the interface itself is phase-1/phase-2 design work.

## Non-negotiables (from AGENTS.md — must survive the rebuild unchanged)

- Observations, reported claims, inference, and attributed scenarios stay distinct
- Provenance and temporal versions are preserved
- Review remains append-only (proposal/decision/accepted-version history)
- No invented coordinates or geometry; unresolved locations stay honestly unresolved
- The renderer can never mutate accepted facts — a geography/map failure must not corrupt evidence state
- Synthetic fixtures stay marked and separate from real evidence (the copper pilot's role as review fixture is unaffected by this rebuild)

## Phasing (proposed, implicitly accepted — not yet detailed into implementation plans)

1. **Foundation.** Fork God's Eye, strip features one-by-one, testing after each removal — the same bisection method that actually found the Cesium dependency bug, now applied deliberately rather than as an emergency debugging tool. Arrive at a minimal TypeScript shell: globe, camera, hover, HUD chrome, scene-director skeleton, share-links, global-context — no live data, no Nexus data yet. Expose the action-layer API skeleton from the start even before real data is wired in, since retrofitting it later is the expensive path.
2. **Data adapter.** Replace God's Eye's live-feed layer system with an adapter reading Nexus's entity registry (industry-scoped, via the existing FastAPI backend). Implement the metric→entity linkage, the significance/LOD system, and the reconciled type taxonomy from this phase's research.
3. **Evidence & review UI on the new foundation.** Rebuild the review workflow, relationship graph, evidence inspector, and metrics view as views within the new shell, talking to the same FastAPI backend. Nothing here requires backend changes beyond what phase 2 already needs.

## Open questions (not yet decided — need resolution before writing phase 1's implementation plan)

- **Migration sequencing:** big-bang cutover once phase 3 reaches parity, or run the new shell alongside the current React app until it's ready? What's the first genuinely shippable milestone?
- **Action-layer concrete interface:** verb list, argument shapes, how it's exposed to React state vs. the Cesium-adjacent shell code.
- **Entity/type migration mechanics:** exact re-ID scheme for existing oil/copper entities: PostgreSQL migration to write, whether old ids need to remain resolvable (e.g. for existing review history referencing them) or whether review history itself gets migrated.
- **Test strategy:** God's Eye uses `node:test` `.mjs` files; Nexus uses pytest (backend) + Playwright (e2e). Whether stripped-and-adapted God's Eye modules keep their existing test style or get converted.

## Information design and guided tours (in discussion, 2026-09-23)

**User-stated requirement.** Someone entering an unfamiliar industry should get a guided tour covering: the current state; the main suppliers and which countries they are in; where production happens, what the materials are and where they are sourced; how the industry developed over the past decade or two, plus a brief history where records exist (authoritative articles may be sourced instead of reconstructed); how geopolitics has shaped it; what the commodity is used for; future developments and outlooks; and opportunities for a student.

**User-stated open questions**: how much of the work is Nexus's own analysis versus reliance on authoritative external sources; whether agents need analytical scaffolding (for example chart-making scripts) and how far it can go; how to decide what data and graphs to show when industries differ, and whether an LLM can pick; how far LLM reasoning can be trusted.

These are unresolved. Related design records: the action-layer principle above, and `docs/data-acquisition.md` for how evidence enters the system.

**User decisions, 2026-09-23:**
- **Dark visual style**, in the God's Eye tradition.
- **The globe is the centrepiece and stays in the background**; other screens layer on top of it, as in God's Eye. Exact behaviour per screen is still to be mapped.
- **Guided tours advance on "next"**, not automatically.
- **Desktop first.** Narrow layouts degrade gracefully; mobile is not a target.
- **Tours are curated**, one per major industry, with some form of generation so they can be updated as data changes.
- **Budget constraint:** a hosted version costing more than about $10 to $20 a month is not viable. Community growth might change that later.

**User leanings, not decisions, sent for technical evaluation** (see `docs/briefs/technical-design-review-brief.md`):
- Where sources report different numbers, show an interval with citations instead of a single hard number.
- Model shipping as a network of real major lanes, like highways, with smoothed on-ramps and off-ramps for individual routes.

**Next:** refine the user-facing flows in `docs/ui-flows.md`, which holds the first-pass screens and diagrams and the second round of user decisions (2026-09-23).

### Data conditions and warnings (proposal, not decided)

The user wants edge cases and missing data to be shown clearly rather than hidden, for example a visible marker when a location is not found. The data already carries most of the signal: `location_precision` (`unresolved_geometry`, `unresolved_route`, `country` and others), `location_note`, claim `caveat`, `review_status`, null `valid_from`/`valid_to`, and metric `status`.

| Condition | Meaning | Proposed treatment |
|---|---|---|
| Not applicable | Structurally has no location (a material, an industry) | No warning. Absent from the map, with a tooltip explaining why. |
| Unresolved | It exists but its location or geometry is not yet sourced | Never a guessed point. Listed in a "not on map" tray with a HUD-style "NO FIX" marker. |
| Coarse | Only country or region precision is sourced | Drawn at that geometry with a precision chip. |
| Unknown | Sources are silent (for example validity dates) | The word "Unknown", never a blank. |
| Estimated / forecast | Already labelled in metrics | Unchanged. |
| Conflicting | Sources disagree | Show both, attributed. Never average silently. |
| Stale | Older than the industry's freshness threshold, or the source changed since packaging | Age chip. |
| Unverified | Excerpt not machine-verified, or source unreachable | Chip in the verify drawer. |
| Unreviewed | Candidate, not yet accepted | Exists today. |
| Incomplete chapter | A tour chapter lacks evidence for a required slot | A gap card inside the tour. |

Principles: absence is always rendered explicitly. Three severities: a quiet glyph, a visible chip, and an inline replacement when a figure or chart cannot be produced safely (for example mixed units). Icon plus text, never colour alone. Not-applicable stays silent to avoid alert fatigue. Gaps are records (kind, subject, reason, since), so curators get a backlog, packs can list their known gaps at install, and the chat agent is told about them and answers "unknown" instead of guessing.

## Provenance of this document

Synthesized from a multi-turn design conversation on 2026-09-22, after the Cesium rendering bug (see `docs/development-log.md`) was found and fixed. Decisions above marked "Checked against current data" were verified against the actual `evidence-pack.json` files at the time of writing, not assumed. The taxonomy table and traps were produced by a background research agent that fetched and read its cited sources rather than recalling them from training; its explicit unverified/unable-to-access items are preserved above rather than smoothed over.
