# Evidence workbench backend

The application imports one validated research snapshot into PostgreSQL as candidate assertions. Review decisions can accept or reject candidates, and corrections create new proposals against the current accepted revision. The original investigation files remain the research fixture; local review is an editorial decision and never a claim of independent physical verification.

Public module responsibilities:

- `evidence.py`: source metadata and reference validation; no application dependencies.
- `knowledge.py`: entity/assertion/event records, fixture integrity and bounded incident-link traversal. Depends only on Evidence's public contract.
- `review.py`: proposal/decision contracts, correction rules and the storage port. Depends on Evidence and Knowledge, not PostgreSQL or HTTP.
- `investigation.py`: loads and validates the research fixture and authored reading guide. Coordinates through Knowledge's public contract.
- `storage/`: PostgreSQL migrations and repository implementation. The core domains never import it.
- `main.py`: API composition and transport; migrates/imports at startup when PostgreSQL is configured and otherwise serves the read-only fixture.

The read API offers `GET /api/investigation`, bounded neighborhoods, review status and per-claim history. Write endpoints create proposals and decisions. They require the local review header and an allowed local browser origin. Every request has a caller-generated UUID: identical retries are idempotent, while reuse with changed content is rejected. PostgreSQL row locks and expected revisions prevent two reviewers from silently replacing one another.

Date semantics: publication dates, source-as-of labels, event dates/precision and fixture-recorded dates remain distinct. Fiscal-year labels stay labels; missing valid-time bounds and coordinates stay unknown. No historical as-of filtering is implemented.

Proposal, decision, and accepted-version rows are append-only through database triggers. Acceptance atomically writes a new version and advances the head; a failed version write rolls back the decision. Rejection records a decision without advancing the baseline. Source references have database foreign keys. Fixture changes after initial import stop startup until an explicit migration is written.

Tests use synthetic domain records and disposable PostgreSQL schemas, then API and browser checks against the real fixture. They cover competing reviews, stale proposals, idempotent retries, rollback, immutable history, fresh repository connections, and native `pg_dump`/`pg_restore` into a separate database. The import-boundary check is itself tested against forbidden imports.

Backup scripts create non-overwriting custom-format archives under `.local/backups`. Restore always targets a newly named database and refuses to clean or overwrite an existing schema. The project-local PostgreSQL runtime and credentials are ignored by Git.
