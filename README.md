# Nexus

An exploratory supply-chain learning and investigation tool connecting industries, companies, materials, infrastructure, and news through sourced evidence.

## Documentation

- [Product design and phased plan](docs/design.md)
- [Technical stack, deployment options, model routing and costs](docs/technical-stack.md)

Development now includes a selectable oil industry brief and the original copper evidence fixture, backed by PostgreSQL manual review history. The oil brief covers 2025-Q3 through 2026-Q2 with eleven sourced metric groups, selected structural baselines, six guided geographic anchors, two illustrative corridors and developments through mid-September 2026. Its geographic view uses a God’s Eye View-inspired Cesium globe where WebGL is available and a local Natural Earth map fallback elsewhere. Explore relationships, metrics, geography, events, evidence and authored reading guides; accept or reject candidates, propose sourced corrections, and inspect every retained version. See [implementation status and remaining work](docs/development-status.md), the [God’s Eye integration review](docs/gods-eye-integration.md) and the [durable development log](docs/development-log.md).

## Run locally (Windows / PowerShell)

Requires Python 3.11+ (tested with 3.13), Node 22.12+ (tested with 26), npm, and PostgreSQL 17. Use an existing PostgreSQL server through `NEXUS_DATABASE_URL`, or place the official Windows binary archive under `.local/postgres-runtime/pgsql` and run the included setup script. This checkout already has a project-local development cluster. From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements.lock
.\.venv\Scripts\python -m pip install --no-deps -e backend
npm --prefix apps/web ci
.\.venv\Scripts\python scripts/setup-postgres.py
.\scripts\start-local.ps1
```

Open [Nexus locally](http://127.0.0.1:5173). The script ensures the configured database is running, starts two hidden loopback-only processes, prints their stop command and writes logs under `.local/`. Without database configuration the evidence fixture remains readable, while review controls report read-only mode. No API key is required.

Create a timestamped database backup:

```powershell
.\.venv\Scripts\python scripts/backup-database.py
```

Restore an archive into a new database name (the active database is left unchanged):

```powershell
.\.venv\Scripts\python scripts/restore-database.py .local/backups/<archive>.dump --database nexus_restore_check
```

For foreground development, run the API and frontend in separate terminals:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
npm --prefix apps/web run dev
```

## Checks

```powershell
.\.venv\Scripts\python -m pytest backend/tests -q
.\.venv\Scripts\python -m ruff check backend scripts
.\.venv\Scripts\python -m ruff format --check backend scripts
.\.venv\Scripts\python scripts/check_licences.py --mode dev
.\.venv\Scripts\python scripts/normalise.py check
npm --prefix apps/web run format:check
npm --prefix apps/web run build
npm --prefix apps/web run test:e2e
```

Browser tests use installed Microsoft Edge and start the local servers automatically. After changing API models, regenerate the contract and frontend types:

```powershell
.\.venv\Scripts\python scripts/export_openapi.py
npm --prefix apps/web run generate:api
```

The CI definition checks generated contract drift; it has not yet run on a hosted repository. See [development status](docs/development-status.md) for the exact local validation record and [backend ownership and invariants](backend/README.md) for review semantics.

Shared research remains in [Data Atlas](<../Jobs and Shite/research/data-atlas/README.md>) and [conversation memory](<../Jobs and Shite/research/osint-project-memory.md>). These relative links assume the current sibling-folder arrangement.

Architecture research: [Sustainable AI-assisted development](docs/architecture-and-development.md) — proposed module boundaries, contracts, checks and working conventions.

## Accepted baseline and first investigation

The user accepted React/TypeScript, Python/FastAPI and PostgreSQL with a modular-monolith organization, and subsequently authorized development. React/Vite, FastAPI, PostgreSQL and the first real-map integration are implemented for the evidence, manual-review and guided-geography slices; model/provider selection remains unimplemented.

[Industry brief 02: Oil under constraint](investigations/02-oil-system/README.md) is the selected first complete brief. [Pilot 01: Kamoa copper to cable manufacturing](investigations/01-kamoa-to-cables/README.md) remains the evidence-handling fixture.

[Comparable commercial products and design lessons](docs/comparable-products.md): public-documentation research into supplier graphs, shipment visibility and aggregate trade visualization.

Current scope: see the 2026-09-21 section in [design](docs/design.md). Industry-level learning with a guided geographic briefing; selective detail by significance. Earlier exhaustive-chain interpretations and milestone ordering are superseded there.

## Licence

Source code: [MIT](LICENSE). Original authored text (documentation, claim wording, notes, tours): [CC BY 4.0](LICENSE-CONTENT.md). Third-party software, fonts and data keep their own licences: see [third-party notices](THIRD_PARTY_NOTICES.md) and `licences/`. Quoted source excerpts belong to their publishers. Check with `python scripts/check_licences.py --mode release`.
