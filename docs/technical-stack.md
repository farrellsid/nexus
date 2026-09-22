# Nexus: stack and cost decisions

2026-09-15 planning record, updated 2026-09-22. A local application now exists; see [development status](development-status.md). React/TypeScript/Vite, FastAPI/Pydantic, PostgreSQL 17/Psycopg, CesiumJS, Natural Earth/TopoJSON fallback rendering, pytest, Ruff, generated OpenAPI types and Playwright are installed and exercised. The database implements reviewed assertion history; SQLAlchemy/Alembic have not been adopted because the current migration and query surface is small and explicit. No paid service or deployment exists. Earlier unimplemented-tool statements below are historical proposals. Read [product design](design.md) for scope and evidence rules.

## User preferences

Full application in a local repository; optional lighter public web demo, shelved if it complicates the main project. Explore cloud storage only where useful. Allow users to configure provider API keys and models; run workload-specific pilots before choosing defaults. Structure tasks and inputs/outputs in code and consider different model tiers for different work. Record the tradeoffs and measured results for a possible interview case study; do not invent performance claims.

## Recommended starting stack

| Layer | Proposal | Tradeoff / alternative |
| --- | --- | --- |
| Browser workbench | React + TypeScript + Vite, Cytoscape.js graph | TypeScript supports shared UI contracts; skip server rendering initially. A desktop wrapper adds packaging work and is optional. |
| API/domain logic | Python + FastAPI + Pydantic | Useful fit for ingestion and evaluation; two languages require a generated OpenAPI client. All-TypeScript is a valid simpler-language alternative if ingestion needs stay modest. |
| Persistence | PostgreSQL, SQLAlchemy/Alembic migrations | Keep assertions, provenance, review records and jobs together. SQLite simplifies a throwaway prototype but moving databases later adds work. Neo4j merits reconsideration only for demonstrated graph-query needs. |
| Retrieval | PostgreSQL full-text search; pgvector when needed | Keep lexical and semantic retrieval complementary; no separate vector service initially. Evaluate multilingual retrieval explicitly. |
| Document files | Local content-addressed directory with a small storage interface | Add S3-compatible object storage later without changing domain records; database retains metadata and hashes. |
| Jobs | Separate Python worker, same codebase, durable Postgres job records | Lease/claim jobs transactionally; retry with limits; idempotent outputs, cancellation and crash recovery. Avoid a mandatory Redis or distributed workflow service initially. |
| Model access | Small provider adapter layer using official SDKs | Start one provider end-to-end, then a second to test portability. Avoid promising arbitrary models work equivalently. |
| Packaging/tests | Monorepo, local Compose option; pytest and browser workflow tests | Document Windows/Docker setup and offer manual startup. Container tooling/licensing must be checked before distribution. |

Suggested future repository folders: `apps/web`, `backend/app` (domain, API, ingestion, worker, model adapters), `contracts`, `evals`, `fixtures`, `docs`. This is a proposed layout, not directories to scaffold now. Large documents, generated indexes and secrets do not belong in Git; include a small permitted sample and explicit synthetic fixtures. Backups must include both database and referenced objects, and restoration must be tested.

FastAPI exposes OpenAPI and validation capabilities: https://fastapi.tiangolo.com/features/ . PostgreSQL text search: https://www.postgresql.org/docs/17/textsearch-intro.html . pgvector is vector search within Postgres: https://github.com/pgvector/pgvector . These are capability checks, not comparative benchmarks.

## Local app and optional demo

Local-first means the application/database can run on the user's machine; hosted models and research still send selected content to external services. Fully offline inference is a separate stretch goal dependent on hardware and evaluation.

Reuse the same browser components for a read-only static demo exported from one curated investigation. Versioned public export includes permitted entities, assertions, source links, dates and optionally clearly labelled prerecorded answers. It excludes credentials, private source text and raw internal logs. Snapshot timestamp is visible. Mock/replayed answers must not masquerade as live conversation.

This needs only a narrow data-access interface for API versus snapshot reads. Avoid a separate demo fork. A future live demo adds a backend, budgets, rate limiting, abuse controls and isolation. Prefer no public key entry in the first demo. Never bundle a provider secret in frontend code. Keep local user keys in backend environment/OS secret storage, redact logs, and bind the local service to loopback with origin checks. BYOK does not grant paid search/data access or override provider quotas. A hosted BYOK mode needs an explicit key-handling design rather than browser localStorage by default.

## Storage and scale

Do not assume the whole internet must be ingested. Keep selected source versions and bounded graph neighbourhoods. Full PDFs, imagery, parsed derivatives and embeddings can outweigh relation records. Measure disk growth, database index size, memory and query latency before scaling.

Illustrative arithmetic, not a forecast: 10,000 PDFs averaging 2 MB consume about 20 GB before extracted text, versions, indexes and backups. One million 1,536-dimensional float32 vectors consume 6.144 GB in values alone; indexes/metadata add more. Embeddings require model/dimension/version metadata and regeneration planning.

Cloud object storage is appropriate for sharing, backup and a large document corpus; it does not replace a database or provide compute. Cloudflare R2 Standard lists $0.015/GB-month, separate operation charges and free internet egress. Thus 100 GB is $1.50/month in base storage before free allowances and operations. Hosted Postgres, server compute, OCR, search, models and licensed datasets are additional. Source checked 2026-09-15: https://developers.cloudflare.com/r2/pricing/ . No cloud budget or provider has been selected.

## Model routing and BYOK

Use explicit stages rather than a hierarchy of conversational agents by default:

1. Code handles downloading, hashing, duplicate detection, schema/type checks, units, date validation, graph traversal and persistence.
2. A lower-cost candidate model handles classification and proposed passage-level extraction.
3. A capable model handles ambiguous linking, conflicting accounts, research planning and cross-source explanations.
4. Code checks citations and permissions; review decides acceptance. Valid JSON is not proof of factual validity.

Escalate on observable triggers (unresolved candidates, inconsistent evidence, missing support), not merely a model's confidence number. Some cases should remain unknown rather than trigger more calls. Configure roles such as extraction, explanation and research to provider/model IDs. Adapters should declare structured-output/tool/image/streaming capabilities, normalize usage and refusals, cap retries, and preserve provider-specific options. Search and embedding configuration are separate from the chat model. A local model endpoint is an optional adapter, not guaranteed compatibility.

For now, evaluate three workflows: capable-model baseline; inexpensive-model baseline; inexpensive extraction with selective escalation. Compare accepted-claim accuracy, unsupported assertions, entity-linking precision/recall, citation support, missed facts, date accuracy, multilingual performance, latency, token/tool cost and human review time. Use a curated development set plus held-out documents with known ambiguity; compare end-to-end outputs as well as stage-level results. No model quality winner has been established.

Maintain document/prompt/schema/model versions, retrieved evidence IDs, tool calls and normalized usage per run. Do not require hidden chain-of-thought. Cache unchanged extraction by content hash plus prompt/schema/model version; tie answers to graph/evidence revisions. Budget tokens, documents fetched, tool calls, retries and wall time per job; checkpoint and return partial progress at the limit. Queue background ingestion separately from interactive questions.

## Dated pricing examples

Standard paid text-token list prices, USD per million tokens, checked 2026-09-15. Illustrative comparison candidates, not a newest-model ranking or measured quality recommendation. Exclude cached/batch discounts, premium context tiers, reasoning-token variability and tools; verify account access and current terms before using.

| Model | Input | Output | Arithmetic for 10,000 input + 1,000 billed output tokens |
| --- | --- | --- | --- |
| Gemini 2.5 Flash-Lite | $0.10 | $0.40 | $0.0014 |
| GPT-5.4 mini | $0.75 | $4.50 | $0.0120 |
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.0150 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $0.0450 |

Sources: https://ai.google.dev/gemini-api/docs/pricing , https://developers.openai.com/api/docs/models/gpt-5.4-mini , https://platform.claude.com/docs/en/about-claude/pricing . These are token arithmetic only: actual tokenization, reasoning, repeated retrieval, failures and search/OCR fees change workflow costs. Cost per accepted supported claim is a better decision metric than cost per request. Newer models can be added to the pilot after checking pricing and task fit; the application must not hardcode these names as universal defaults.

## Other engineering considerations

- PDF layout, tables, scanned pages and passage coordinates: test a parser/OCR choice on the actual corpus; retain original passages and page references. Avoid choosing a large ingestion framework before seeing failure modes.
- Treat web/documents as untrusted content. Bound fetch size/time/redirects and block private-network targets in research fetchers. Model proposals cannot authorize arbitrary filesystem, shell or graph mutations.
- Identity quality matters more than graph volume: stable IDs, facility/company distinctions, multilingual aliases and reviewable merges.
- Retrieval evaluation must cover original-language evidence and translation; do not overwrite original text with a translation.
- Frontend query limits, pagination and incremental neighbourhood expansion are needed well before a new database. Graph rendering and database capacity are different bottlenecks.
- Separate third-party data rights from source-code licensing; exported demo content needs its own checks.
- Prove a complete startup/import/query/review/revision/export/restore path before adding cloud services or multiple autonomous agents.

Next proposed decision gate: select one small evidence corpus and representative questions, then use the constructed workbench and model pilot to validate this stack. No hardware specifications, hosting budget, coding-language preference or API budget has yet been supplied; do not invent them.


## Architecture follow-up

See [Architecture and sustainable development](architecture-and-development.md) for the recommended modular-monolith structure and verification tooling. These are researched proposals, not installed infrastructure.

## Accepted baseline update

The user accepted the React/TypeScript + Python/FastAPI + PostgreSQL modular-monolith baseline and authorized the first data-feasibility investigation. This supersedes earlier statements that the entire baseline is unselected. No dependencies have been installed; optional libraries, provider, spending budget and hosting remain undecided. Pilot evidence is in ../investigations/01-kamoa-to-cables/README.md.
