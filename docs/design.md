# Nexus — supply-chain learning and investigation explorer

Recorded 2026-09-15, updated 2026-09-22. The user subsequently authorized development and selected oil as the first complete industry brief. A local evidence and review workbench now exists; see [development status](development-status.md). Historical planning statements below describe the earlier discussion, not a restriction on the newly authorized development. Deployment and paid usage remain unrequested. User-endorsed priorities are separated from proposed implementation choices.

## User direction

Help a curious person understand how industries, companies, materials, infrastructure and news connect. Prioritize descriptive analysis: what exists, how production works, who participates, and what relationships are supported. Prediction is a later possibility, not the initial promise.

The Robert Friedland Odd Lots copper interview motivated this direction. Treat it as a participant's narrative and a source of questions, not a verified database. The supplied transcript may contain transcription errors. Original file: `C:\Users\User\Downloads\Odd Lots Podcast on Copper Shortage.txt`.

The eventual scope extends downstream into semiconductors (including TSMC, Samsung, SK Hynix and unfamiliar Chinese companies), aircraft, drones, defense industries and renewables. Company names are interests, not claims about specific supplier relationships. The user wants to learn an unfamiliar industry and situate it within the wider economy. News should provide entry points and illustrate change.

The user welcomed a descriptive, evidence-backed learning/investigation direction. A bounded cross-industry path was proposed instead of a copper-only dashboard. The user subsequently accepted the React/TypeScript + Python/FastAPI + PostgreSQL modular-monolith baseline and authorized a first feasibility investigation. The selected pilot is recorded in ../investigations/01-kamoa-to-cables/README.md. Project schedule and final coverage remain undecided. God's Eye View may provide reusable visualization components after architecture/licence review; reuse has not been selected.

## Proposed architecture

Use a typed, directed graph as the domain model, backed initially by PostgreSQL tables. A graph model does not require a dedicated graph database. Evaluate a graph database later if measured traversal needs justify the extra service.

Entities: organization, facility, location, material/product, process and infrastructure. Give entities stable IDs, aliases and external identifiers; distinguish parent companies, subsidiaries and facilities. Model processes explicitly so several inputs and outputs can belong to one transformation. The system is a network with recycling and feedback, not necessarily an acyclic chain.

Relations: operates, located_in, consumes, produces, supplies, depends_on, participates_in. Separate a generic process requirement from a documented facility/customer relationship. Direction and allowed endpoint types must be defined for each relation. Missing links mean unknown, not proof of no relationship. Qualify relations by product, facility, geography and time where known.

Store assertions separately from their supporting or contradicting evidence. Suggested core tables:

- `entities`: identity, type, names and aliases.
- `assertions`: subject, relation, object, scope, review status, valid-time bounds and date precision; quantities/units where available.
- `documents` and `document_versions`: canonical URL, publisher, publication/retrieval timestamps, content hash and permitted content storage.
- `passages`: retrievable evidence with page/section/offset locators.
- `assertion_evidence`: many-to-many links, including support/contradiction and extraction provenance.
- `events`: dated changes linked to entities and source assertions; distinguish announcement, expected completion and actual operation.
- `assertion_versions` / review records: retained changes, supersession and who/what made or accepted them.

Do not make every extraction an accepted graph edge. Keep candidates and contested assertions available without presenting them as established. An LLM confidence score is not a calibrated probability. Preserve separate source, extraction and review information.

## LLM interaction

Use retrieval-augmented generation over both graph facts and document passages. For a question, resolve the named entities, retrieve a bounded neighbourhood filtered by date/status, retrieve relevant passages with lexical and optionally vector search, then provide evidence IDs to the model. The graph supplies structure; original passages supply detail and provenance.

Expose bounded read tools such as entity search, neighbourhood lookup, evidence retrieval and event lookup. Have answers cite passages and distinguish supported relationships from possible mechanisms or unknowns. Validate citation IDs against retrieved evidence; evaluate whether passages actually support each answer. Avoid unrestricted model-generated database commands. Retrieved documents are data, not agent instructions.

The UI can highlight the exact nodes and assertions used by an explanation. Start with short neighbourhood exploration rather than putting the entire graph into a prompt. This is graph-assisted RAG; adopting Microsoft's full GraphRAG indexing and community-summary pipeline is optional and requires separate evaluation.

## News and reports

Proposed pipeline: selected document/URL or permitted feed -> retain metadata/permitted version -> extract text and source locators -> resolve entities -> propose assertions/events -> review changes -> publish accepted views and retrieval index.

News discovery (including GDELT) is distinct from access to full article bodies. Consult Data Atlas for provider restrictions. Store full text only when permitted; otherwise retain links, metadata and permitted excerpts. Do not equate several syndicated copies with independent corroboration. Deduplicate canonical URLs/content and retain origin relationships. Report publication date is not necessarily the date its facts apply.

Initially, users select a small set of reports and historical stories and approve proposed entries. Use the same ingestion/review interface later for periodic retrieval. Automation should first discover updates and draft a change queue. Explicitly account for aliases, changed facilities, corrections, contradictory accounts and recurring failed fetches. Only consider automatic acceptance later for narrow, structured sources with validated mappings. No polling or automation is being scheduled by this design.

## History from the beginning

Keep two kinds of time: valid time (when a relationship reportedly held in the world) and recorded time (when this system acquired/accepted that assertion). Also retain publication and retrieval time. A report published in March can describe a January ownership change; a later correction must not erase what the system knew in March.

MVP: timestamped versioned assertions, document versions, non-destructive corrections and explicit unknown/approximate dates. Later: as-of graph queries, date comparison, history slider and selected historical backfills. Reconstruct only supported historical periods; never silently present today's relationships as historical truth. No need to snapshot the whole graph daily. Retention of source content remains subject to rights.

## Earlier scope ladder (superseded by the 2026-09-21 scope below)

| Capability | MVP | Later |
| --- | --- | --- |
| Coverage | One selected path spanning production stages and downstream use | Multiple intersecting industries and regions |
| Graph/UI | Small expandable graph, entity explanations, evidence panel | Rich map/globe, comparative views, guided investigations |
| Data entry | Curated documents; manual entry or reviewed extraction through one pipeline | Feed discovery, change queue and narrowly validated automatic updates |
| Conversation | Bounded graph/passages retrieval, citations and unknowns | Cross-industry synthesis, more sophisticated retrieval and voice |
| News | A few sourced historical stories linked to entities/events | Ongoing news ingestion and clustering |
| History | Preserve dates, versions and corrections | As-of exploration, backfills and comparisons |
| Analysis | Describe production and supported relationships | Scenarios, then separately evaluated predictions |

Illustrative planning size: tens of entities and a small document collection, enough to demonstrate one meaningful cross-industry path. This is a suggested scope, not an agreed count or time estimate.

Suggested first acceptance checks: explain an unfamiliar production stage; trace a supported path with evidence for every edge; answer a company question with precise citations; return unknown for an unsupported supplier query; retain both versions of a correction; avoid treating a repeated article as independent evidence. Test entity resolution and date handling on deliberately ambiguous examples. Do not measure success by graph size or visual density.

## Technology candidates and evidence

Detailed follow-up: [stack, deployment, model routing and costs](technical-stack.md). This refines the earlier candidates and keeps local execution primary, with an optional snapshot-based web demo.

Proposed lean stack: PostgreSQL for structured records and text search; a small API/ingestion worker in the developer's preferred language; a browser UI with Cytoscape.js for graph interaction; one model integration for retrieval-based answers. Add vector search when paraphrase retrieval justifies it, and map rendering when geography helps answer the chosen questions. The core stack baseline is now accepted; detailed library choices remain proposals and nothing has been installed.

- PostgreSQL supports recursive queries for traversing linked records: https://www.postgresql.org/docs/17/queries-with.html
- Cytoscape.js provides browser graph visualization and analysis: https://js.cytoscape.org/
- Microsoft's GraphRAG local search combines entity-neighbourhood information with source material: https://microsoft.github.io/graphrag/query/local_search/
- GraphRAG has distinct local/global query approaches: https://microsoft.github.io/graphrag/query/overview/

Primary documentation checked 2026-09-15. These substantiate capabilities, not a benchmark or integration test.

## On-demand research and attributed scenarios

User-originated extension: a question outside the ingested collection, such as the effect of a hypothetical US tariff on selected metals and semiconductor production, could trigger multilingual research and produce an explorable, source-attributed scenario. The user welcomed this direction. This does not authorize implementing autonomous research yet.

Proposed flow: clarify material/product scope, jurisdiction, time horizon and hypothetical versus enacted policy -> inspect existing evidence -> research missing claims -> retain original passages and labelled translations -> draft entities/assertions/events -> show evidence and proposed changes -> save a reviewed scenario.

Keep documented structure, enacted/reported changes, a source's forecast and the system's additional inference distinct. A report's predicted supplier switch must not overwrite the baseline supplier relationship. Scenarios should reference a baseline revision, source versions, explicit assumptions and dated claims. Users could compare different reports' scenarios and inspect disagreements. New descriptive facts discovered during research can enter the normal review queue separately.

Citations do not establish correctness or applicability by themselves. Check that each passage supports the proposed claim for the relevant materials, places and dates. Preserve dissent, missing evidence and qualifications. A qualitative source does not authorize invented quantitative impacts. Source-attributed scenario exploration can precede a proprietary prediction model and should precede autonomous worldwide monitoring.

Updating supply-chain services discussed as discovery leads: Panjiva/S&P Global and Altana, plus event/news and policy sources such as GDELT and WTO notifications. Provider product pages were reviewed in conversation, but access, licensing, latency, completeness and integrations have not been audited for these new commercial leads. No open comprehensive live supply-chain feed has been established. Do not promote these leads to verified Data Atlas records without a separate provider audit.

## Development sequence: analysis first, geographic interface later

User proposal: pilot the analysis/graph layer in a constructed environment, independently of complex world-map rendering. Once useful, evaluate forking God's Eye View, removing unnecessary features and integrating the working capabilities. Desired eventual interaction: explore an Australian mine, follow its chain and navigate to relevant physical sites. No actual mine or relationship has been selected. The user requests ongoing updates to docs/plans as discussion develops; this is not authorization to start implementation.

Recommended architecture boundary: one domain service for entities, assertions, evidence, dates and scenarios; interchangeable graph and geographic views consume the same IDs and queries. The analysis code must not depend on a globe renderer, camera state or God's Eye internals. No microservice split is required: a modular application is sufficient initially.

An initial workbench should include an expandable graph, entity/evidence panel, question interface and proposed-change review. Use a small explicitly synthetic fixture to exercise cycles, multiple inputs, conflicting accounts, missing locations and revisions. Keep synthetic records visibly marked and excluded from the real evidence collection. Follow promptly with one small real, sourced path to test identity resolution, uneven documents and missing relationships; successful synthetic behaviour alone is not evidence of real-world feasibility.

Earlier proposed milestones (superseded by the 2026-09-21 sequence below):

1. **Constructed workbench:** inspect relations/evidence, expand nodes, ask bounded questions, and review a change. Preserve versions and baseline/scenario separation. Demonstrate an unsupported question returning unknown.
2. **Real evidence pilot:** load one chosen cross-industry path and a few reports; verify citations, ambiguous entities, contradictions and updates. Determine whether a newcomer can explain the chain afterward.
3. **Research extension:** a user-triggered unknown question retrieves permitted sources and proposes a reviewable scenario; original graph remains intact.
4. **Geographic integration trial:** inspect God's Eye architecture, licence and data dependencies. Prototype selecting one real facility and focusing it in a map, then selecting a second site without losing graph/evidence context. Choose a fork or extracted components based on that trial rather than assuming either will be easy.
5. **Broader geography and updates:** linked navigation across supported facilities, ongoing ingestion/change queues, historical comparisons and broader coverage. Autonomous acceptance and quantitative forecasting remain later work.

Design the geographic contract early, even before rendering: stable entity IDs; facility coordinates/geometry with source and precision; explicit unknown locations; selected entity; current time filter; active scenario; bounded visible subgraph. Abstract processes/materials need not have coordinates. A headquarters point must not substitute for an unknown factory. Suggested view actions include select entity, expand neighbourhood, show evidence and focus a located facility.

Supply links represent documented relationships, not necessarily physical transport routes. A drawn line must not imply a known vessel, route or shipment. Label why a location is relevant; reserve 'critical' or 'bottleneck' for a defined, supported criterion rather than visual prominence or graph degree alone.

Geographic trial acceptance: graph-to-map and map-to-graph selection use the same entity; absent coordinates remain absent; switching views preserves date/scenario/evidence state; source passages stay reachable; the renderer cannot mutate accepted facts. Keep the workbench usable after geographic integration for debugging and evidence review.

Related files: [project memory](<../../Jobs and Shite/research/osint-project-memory.md>), [Data Atlas](<../../Jobs and Shite/research/data-atlas/README.md>). Source-provider claims belong in editable Data Atlas records and should be rebuilt there; this note contains product direction and proposed architecture.




## Current scope and milestones — 2026-09-21

This section supersedes the earlier coverage target and milestone ordering where they conflict. Evidence, temporal history, modular architecture and independent analysis testing remain applicable.

### User direction

Nexus explains industrial systems and developments shaping them, at the level of countries, sectors, major companies, material flows and important infrastructure. Exhaustive small-supplier, customer or retail-outlet tracking is outside the goal. Detail follows explanatory significance: a small supplier can still merit inclusion when a supported bottleneck makes it important.

The user wants a geographically guided answer to questions such as "What's happening with oil?": move between relevant locations such as Hormuz, Saudi infrastructure and Chinese demand regions/industries while explaining evidence and quantities. On 2026-09-22 the user selected oil as the first complete industry brief. The copper pilot remains an evidence-handling and review fixture.

### Proposed scale and sources

First end-to-end release: oil, with an observed window from 2025-Q3 through 2026-Q2 and selected developments through 2026-09-10. The current pack contains a curated collection of public documents, six metric groups and 21 meaningful entities rather than comprehensive global coverage. Preserve the copper pack as an evidence-handling fixture.

Combine three source functions: structural context (production processes and major infrastructure); quantitative baseline (production, consumption, stocks, trade and capacity); developments (news, disclosures and official announcements). Add reports and research as attributed interpretation. Countries publish statistical releases and ministry/agency reports on varying schedules; do not expect a universal national quarterly report.

Source leads checked at documentation level on 2026-09-21:
- GDELT multilingual news discovery: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/ . Discover original reporting; retain language and translation provenance. News discovery does not establish full-text reuse rights or event truth.
- EIA energy statistics/API: https://www.eia.gov/opendata/ . Separate historical observations from forecasts.
- JODI monthly oil statistics: https://www.jodidata.org/oil/database/overview.aspx . Assess country/series coverage, reporting lag and revisions before selecting a sample.
- Company annual/interim reports, operational updates, national statistics/customs releases and infrastructure operator publications remain source categories to select and test.
These leads are not newly verified Data Atlas integrations; no endpoints were sampled in this update.

### Revised proposed milestones

1. **Industry evidence brief:** choose industry, date window and representative questions; assemble a small structural map, quantitative series and dated developments. Show units, periods, gaps and original evidence. Existing copper feasibility research partly supports this work but does not complete an oil brief.
2. **Analysis workbench:** implement bounded graph exploration, facts/charts, source inspection and cited question answering independently of geographic rendering. Test unsupported questions, conflicting accounts and corrections. Use manual entry/reviewed ingestion first.
3. **Guided geographic MVP:** link explanations to verified locations and regions, with selectable briefing stops, camera focus, relevant charts and accessible citations. Reuse the analysis state. Prototype the renderer here; assess God's Eye reuse separately. A simple map can establish behavior before a 3D globe. This is part of the intended first end-to-end experience, not a dependency of the analysis engine.
4. **Updating briefings:** add bounded multilingual discovery, deduplication, reviewed document changes, freshness indicators and historical comparisons. Preserve differing release cadences instead of implying all evidence is live.
5. **Broader investigations:** connect additional industries, on-demand multilingual research, attributed scenarios, optional voice and a public snapshot demo. Quantitative prediction is separate stretch work.

An initial guided answer may be manually curated; automatic generation of a reliable tour is later work. Each stop should identify entity/region, supported geometry, date range, claim/evidence IDs, relevant metric and why it matters. UI actions are validated against existing records; missing coordinates must not produce invented points. Regional demand is represented at regional resolution rather than pinned to an arbitrary factory. Geographic mention extraction alone is insufficient to locate an event.

MVP success: a learner can explain the industry's major production/use stages, identify supported important locations and quantities, understand selected developments, inspect the evidence, and recognize what is unknown. No promise to attribute every price movement or predict prices. No schedule, budget, commercial subscription or automatic monitoring is established.

Current status: the workbench can switch between the initial oil brief and copper fixture. Oil includes sourced relationships, metrics, developments, an authored reading guide and a guided real-map view. The geographic renderer adapts the narrow Cesium viewer/source seam from God’s Eye View and falls back to a local Natural Earth map when WebGL is unavailable. PostgreSQL retains manual proposals, decisions, corrections and accepted versions for both investigations. Sourced route/area geometry and model evaluation remain incomplete. Accepted React/TypeScript + Python/FastAPI + PostgreSQL modular monolith unchanged. See [development status](development-status.md) for boundaries and validation.
