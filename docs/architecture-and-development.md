# Architecture for sustainable AI-assisted development

Research date: 2026-09-15. Implementation update 2026-09-21: the accepted modular-monolith baseline now has a read-only Evidence/Knowledge/Investigation workflow, generated API types, import-boundary tests and browser checks. See [development status](development-status.md) and [backend ownership](../backend/README.md). Other architecture/tooling below remains proposed unless explicitly recorded as implemented. This document addresses coding-agent context limits; it is distinct from the application's own research-agent design.

## Recommendation

Use a modular monolith organized around domain capabilities, feature-oriented use cases inside modules, and ports/adapters at external boundaries. Enforce dependencies, contracts and core invariants in automated checks. Retain the proposed Python/TypeScript/PostgreSQL stack. A larger context window, small files or a second agent cannot substitute for dependency management and independent verification.

These are complementary ideas at different levels, not competing frameworks. Older foundational patterns remain applicable to current AI-assisted development. Their benefit here is a design inference, not a measured guarantee of agent reliability.

## Architectural approaches compared

| Approach | Meaning | Nexus decision proposal |
| --- | --- | --- |
| Modular monolith | Internally separated capabilities shipped as one application | Adopt. API and worker may be separate processes from the same codebase/release. |
| Domain-driven design / bounded contexts | Explicit ownership and vocabulary within each domain | Use lightly to define evidence, knowledge and investigations; avoid elaborate aggregates before needed. |
| Vertical slices | Group use-case implementation around changes such as accepting a claim | Use within modules; do not duplicate critical domain rules across slices. |
| Hexagonal / ports and adapters | Core behaviour calls interfaces implemented by storage, models, search and renderers | Use at volatile external boundaries; avoid an interface for every trivial function. |
| Traditional global layers | All controllers, services and repositories grouped by technical role | Avoid as the primary organization: one feature can otherwise scatter across the whole codebase. |
| Microservices | Independently operated services communicating across network boundaries | Defer. Deployment, distributed transactions and partial failures add context rather than inherently saving it. |
| CQRS | Distinct command and query models | Use separate write operations and read DTOs when helpful; no separate databases required initially. |
| Event sourcing | Reconstruct state from a complete event log | Defer. Versioned assertions/audit history meet current needs without full replay infrastructure. |
| Event-driven processing | Work triggered by messages/events | Use narrowly for durable ingestion/indexing jobs; avoid an implicit global event bus. |

Sources: [bounded contexts](https://martinfowler.com/bliki/BoundedContext.html), [vertical slices](https://www.jimmybogard.com/vertical-slice-architecture/), [ports and adapters](https://alistair.cockburn.us/hexagonal-architecture), [microservice tradeoffs](https://martinfowler.com/articles/microservice-trade-offs.html). Technology names do not establish actual isolation; checks and ownership must implement it.

## Proposed module map

Start only the modules exercised by the first pilot. These boundaries are hypotheses to validate with real changes.

| Module | Owns | Public operations / boundaries |
| --- | --- | --- |
| Evidence | Source metadata, permitted document versions, passages and locators | Register/read evidence; stable version and passage IDs |
| Knowledge | Entity identity, aliases, reviewed assertions, temporal versions | Propose/review assertions, resolve entities, query dated relationships |
| Ingestion | Parsing and extraction runs, candidate batches and job progress | Produces proposals through Evidence/Knowledge APIs; cannot bypass acceptance rules |
| Investigations | Questions, evidence selections, runs, scenarios and budgets | Orchestrates public APIs; scenarios never replace accepted facts |
| Retrieval | Rebuildable text/vector indexes and query composition | Reads supported views; returns evidence IDs and revision information |
| Workbench | Graph, evidence, conversation and eventual map interface | Uses application API and generated client; no ORM/database access |

Knowledge may depend on Evidence's stable public reference-validation contract. Evidence does not depend on Knowledge or Ingestion. Ingestion and Investigations coordinate through public operations; neither is an internal dependency of Knowledge. Retrieval consumes public read views and cannot mutate authoritative facts. External SDK and storage implementations are adapters wired at application startup, outside core business rules. Keep shared types limited to stable primitives; a giant shared utils/model package recreates coupling.

One database is acceptable, but each table has a named owning module. Other modules may not mutate it directly or import the owner's ORM models. Cross-module reads use APIs or explicitly documented read views. Foreign keys/constraints and owner APIs preserve integrity; an import linter alone cannot prevent ad hoc SQL. Integration tests and review inspect these bypasses. One ordered migration history tracks schema changes initially.

For accepting an assertion, the Knowledge operation validates evidence references, writes the new assertion version and audit information atomically, and records any required reindex job in the same transaction. A worker processes that job idempotently and records its indexed revision. This prevents a successful write followed by a lost indexing notification. Reads must identify stale indexes; freshness cannot be inferred from successful job submission. No distributed exactly-once promise.

## Contracts that make local reasoning possible

A public operation needs more than field types: define field meanings, accepted states, errors, side effects, provenance, time semantics, ordering/pagination, retry behaviour and idempotency where relevant.

Generate frontend API types from one backend OpenAPI source and fail CI on uncommitted generated drift. Validate actual requests/responses at runtime boundaries. Do not hand-maintain two competing schemas. JSON validity and compatible types do not establish behavioural compatibility.

Examples of project invariants to encode:

- Accepting a descriptive assertion requires valid retained evidence references and a review record.
- A scenario cannot mutate the accepted baseline.
- A correction preserves the previous assertion version and when it was known.
- Reprocessing an identical ingestion job does not duplicate accepted records.
- Unknown facility coordinates stay unknown; a headquarters location is not silently substituted.
- An answer's citations refer to evidence actually retrieved for that run.
- Document instructions cannot grant model tools new authority.

Version exported demo schemas, background-job payloads, model outputs and embedding configuration. Keep old queued payloads compatible during changes or explicitly drain/migrate them. For public contracts and persistence, use additive changes, migrate consumers/data, then remove old fields. A type-compatible change from unknown to false can still be a semantic breaking change.

## Enforcement and tool selection

| Concern | Initial candidate | Notes |
| --- | --- | --- |
| Python dependencies | Import Linter | Declare forbidden, layered and independence contracts; test the checker with a deliberately forbidden fixture |
| TypeScript dependencies | ESLint restricted imports with explicit public entry points | Add Nx only if project graph/task management warrants it |
| Types/style | TypeScript strict checks; Python type checker and Ruff | Catch a useful subset, not business correctness |
| API contracts | Generated client, schema checks and consumer behaviour tests | Add Schemathesis for schema-generated edge cases once APIs exist |
| Domain rules/history | pytest plus Hypothesis where sequences/invariants matter | Real database integration tests for constraints, transactions and migrations |
| User flows | A few Playwright workflows with controlled fixtures | Import -> review -> explore -> cite -> revise -> export |
| LLM quality | Versioned evaluation corpus, held-out cases, stage and end-to-end metrics | Separate from deterministic CI; real API runs need budgets |

[Import Linter](https://github.com/seddonym/import-linter) checks Python imports. [Nx module boundaries](https://nx.dev/docs/features/enforce-module-boundaries) supports JS/TS lint rules; its language-agnostic Conformance enforcement requires an Enterprise plan, so do not assume free cross-language enforcement. [Schemathesis](https://schemathesis.readthedocs.io/en/stable/quick-start/) generates API test cases from schemas. [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html) exercises sequences of actions. [Pact's distinction](https://docs.pact.io/consumer/contract_tests_not_functional_tests) explains why consumer/provider agreement and functional correctness require different checks; a Pact broker is unnecessary for our initial single-release application.

Proposed CI: formatting/types/dependency rules -> domain and real-DB integration tests -> API/client consistency and migration checks -> a small end-to-end suite. Run the full affordable deterministic suite on each change initially. Selective/affected tests are an optimization once dependency tracking is trustworthy; shared schemas, migrations, dependencies and build changes need broader checks. Checkers must be demonstrated to fail on representative bad changes, not merely pass on an empty application.

## A repository that survives context loss

Use progressive reading, not a mandatory dump of every document:

- Root AGENTS.md: short non-negotiable rules, verified setup/check commands and a document map.
- Architecture overview: modules, allowed dependencies, owning tables and key invariants; a C4 context/container view is enough initially.
- Module README: purpose, public operations, dependencies, invariants, representative tests and traps. Target roughly a page, not an artificial token/file limit.
- ADRs: short decisions with status, context, alternatives, consequences and revisit triggers. Preserve superseded decisions with links.
- Task note for sustained work: intended behaviour, non-goals, affected consumers, evidence/tests, current state and remaining work. Record facts/commands rather than hidden reasoning or a transcript dump.

[ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) preserve decision rationale. [C4](https://c4model.com/diagrams) provides progressively detailed architecture views and does not require every diagram level. [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md) has path-dependent loading; do not assume every nested instruction is loaded merely because a file is edited. Explicitly read the relevant module guidance. [Anthropic's long-running harness report](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) describes incremental work, durable progress and verification across context windows; it is an engineering report, not proof of universal reliability.

Keep an architecture index concise and check its paths. Generate inventories/dependency graphs where possible; record intent manually. Avoid duplicate descriptions of schemas. If ordinary changes require nearly every module's internals, revisit the boundary instead of merely increasing context limits. Some changes genuinely cross boundaries and require a larger plan.

## Change workflow

1. Read root/module guidance and reproduce the issue or state the intended behaviour.
2. Identify touched public contracts and consumers, migrations, historical data and cached/indexed results. Search dependencies before coding; local edits do not imply local impact.
3. Define observable acceptance checks; add a regression test when fixing a behaviour bug. Tests should protect requirements, not copy the implementation.
4. Make a cohesive change through owner APIs. Separate unrelated refactoring; do not weaken tests or architectural checks solely to make the change pass.
5. Run relevant checks and the CI gate; inspect the complete diff, generated changes, docs and runtime effects.
6. Record what changed, tests actually run and residual uncertainty. Leave a reproducible handoff on interruption; never label completion solely because a context window ended.

If multiple coding agents are later explicitly used, assign ownership of non-overlapping modules and have one integrator for shared contracts/migrations. Separate worktrees prevent filesystem collisions but do not prevent semantic conflicts. Review against acceptance criteria and consumer tests; another model's approval is supplementary evidence, not a correctness guarantee.

## Decision gate before implementation

Recommended to settle: modular monolith; domain ownership; ports at external seams; feature-oriented use cases; evidence/history invariants; executable dependency/API checks; progressive documentation and small verified changes. Leave exact graph/database scaling, provider choices, orchestration frameworks, cloud and globe integration reversible.

The first implementation should prove one cross-module workflow with tests and enforced boundaries before generating every planned module. No packages or CI configuration were installed by this research task, and none of the proposed checks have yet run against Nexus code.

## Readability and organization

User requirement: Nexus must remain neatly organized and readable for human developers, independently of coding-agent context limits. The following conventions operationalize that priority; tooling choices remain proposals until implementation.

- Organize by cohesive domain capability, with use cases easy to locate. Introduce folders when they contain real responsibilities, not to fill an architectural template. Keep a consistent small module structure and explicit public entry points.
- Use domain vocabulary consistently: document, passage, assertion, evidence, scenario and revision have distinct meanings. Prefer descriptive names such as `accept_assertion` over vague names such as `process_data`. State units and time semantics in names/types where ambiguity matters.
- Keep functions focused on one coherent operation and control flow straightforward. Avoid arbitrary line-count limits, excessive one-line helpers and deep navigation through wrappers. Extract an abstraction when it clarifies a responsibility or a demonstrated shared policy, not merely because code looks similar.
- Keep core rules separate from transport, persistence, model SDKs and rendering. Maintain dependency direction without adding a class, interface or factory for every function. Prefer explicit inputs and results over hidden global state and import-time side effects.
- Keep shared code small and purposeful. Do not accumulate unrelated helpers in a general utils module; locate them with their owning domain or give them a precise shared responsibility.
- Use explicit types at public boundaries, clear error semantics and consistent return shapes. Do not silently swallow failures or use broad fallback behaviour that disguises missing evidence or invalid state.
- Comments explain intent, constraints, non-obvious decisions and tradeoffs. Public API documentation explains semantics and examples. Avoid narrating obvious statements or duplicating information generated from schemas.
- Adopt one formatter/linter configuration per language and use it consistently. Keep generated clients and other generated artifacts visibly separate; regenerate them instead of editing them manually. Check in lockfiles and a reproducible setup procedure when dependencies are introduced.
- Make tests readable examples of expected behaviour. Name them for the behaviour they protect, use small explicit fixtures, and avoid elaborate test helper frameworks that hide the scenario.
- Remove obsolete application code and stale comments as features change. Historical data and migrations follow their retention/compatibility rules and are not dead code to delete. Track meaningful TODOs with context rather than leaving unexplained placeholders.
- Keep changes cohesive and reviewable; do not mix unrelated cleanup with behavioural changes. Update module guidance when ownership or contracts change.

Human readability review: can someone locate a feature, trace its main execution path, identify its state changes and errors, and understand its tests without reconstructing unrelated modules? Evaluate that alongside automated checks. Consistent formatting alone is not evidence that a design is understandable.
