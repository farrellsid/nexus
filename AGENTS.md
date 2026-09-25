# Nexus project guidance

Read `README.md`, `docs/design.md`, and `docs/technical-stack.md` before project work. Keep these documents current as decisions evolve; distinguish user decisions from assistant proposals. Nexus is the chosen project name and this folder is the home for documentation and future implementation.

Prioritize descriptive, evidence-backed learning. Keep observations, reported claims, inference, and attributed scenarios distinct. Preserve provenance and temporal versions. Test the analysis workbench independently of globe rendering; use explicitly marked synthetic fixtures followed by a small real evidence pilot.

Current status: development authorized; the M5 visual shell (`apps/shell`, branch `m5-shell`, see `apps/shell/README.md` and `apps/shell/UPSTREAM.md`) is built and awaits the user's Edge check; the copper workbench and PostgreSQL-backed manual review/version history are implemented. Read `docs/development-status.md` for actual checks and remaining scope, `backend/README.md` for invariants, and `README.md` for setup. This is not authorization to deploy, schedule monitoring or incur costs.

Read `docs/development-log.md` for the latest durable checkpoint and update it during multi-step work so implementation state and immediate next actions survive context limits.

The shared source catalogue is at `D:/Projects/Jobs and Shite/research/data-atlas/README.md`; conversation history is at `D:/Projects/Jobs and Shite/research/osint-project-memory.md`. Provider-documentation review, sample checks and integration validation are distinct. Do not claim all discovery links are verified.

Architectural research and proposed conventions are in docs/architecture-and-development.md. Consult it when discussing or implementing module boundaries; it distinguishes recommendations from accepted decisions and implemented checks.

User priority: maintain a neatly organized, human-readable codebase as well as supporting AI-assisted development. Follow the readability and organization conventions in `docs/architecture-and-development.md`: cohesive domain modules, precise names, straightforward control flow, purposeful abstractions, explicit boundaries, readable tests and comments explaining intent. Avoid arbitrary file-size limits, speculative scaffolding and unnecessary layers.

The user has now accepted the React/TypeScript + Python/FastAPI + PostgreSQL modular-monolith baseline and authorized a first data-feasibility investigation. Read investigations/01-kamoa-to-cables/README.md before pilot implementation. Library specifics remain proposals; acceptance cases are authored, not executed, and source-checked claims are not independent physical verification.

Read the 2026-09-21 current scope section in docs/design.md before further work. Prioritize industry-level understanding and selective significant infrastructure/entities, not exhaustive supplier tracking. The first guided geography is implemented with a God’s Eye View-inspired Cesium path and a Natural Earth fallback; read `docs/gods-eye-integration.md` before extending it. The user selected oil as the first complete industry brief; preserve copper as an evidence and review fixture.
