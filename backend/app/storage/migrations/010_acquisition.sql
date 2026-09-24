-- Acquisition log: every fetch attempt, the content it produced, extractions of that content, the
-- baseline a source is compared with, and each verification result. All tables are append-only.
-- Bytes are never stored in the database; `fetch_attempt.stored` says whether the local object
-- store kept them. A verification without a baseline is recorded as not ready, never as a match.
CREATE TABLE fetch_attempt (
    id uuid PRIMARY KEY,
    source_id text NOT NULL REFERENCES evidence_sources(id),
    requested_url text NOT NULL,
    final_url text NOT NULL,
    redirect_chain jsonb NOT NULL,
    started_at timestamptz NOT NULL,
    ended_at timestamptz NOT NULL,
    status integer,
    content_type text,
    etag text,
    last_modified text,
    byte_count bigint NOT NULL CHECK (byte_count >= 0),
    tool text NOT NULL,
    outcome text NOT NULL CHECK (outcome IN (
        'ok', 'access_denied', 'network_error', 'http_error',
        'blocked_target', 'too_large', 'too_many_redirects')),
    error text,
    sha256 text CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    stored boolean NOT NULL,
    CHECK ((outcome = 'ok') = (sha256 IS NOT NULL))
);
CREATE INDEX fetch_attempt_by_source ON fetch_attempt(source_id, started_at);
CREATE TABLE content_object (
    sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    size bigint NOT NULL CHECK (size >= 0),
    media_type text,
    first_captured_at timestamptz NOT NULL
);
CREATE TABLE source_baseline (
    id uuid PRIMARY KEY,
    source_id text NOT NULL REFERENCES evidence_sources(id),
    sha256 text NOT NULL REFERENCES content_object(sha256),
    text_sha256 text,
    basis text NOT NULL CHECK (length(trim(basis)) > 0),
    reviewer text NOT NULL CHECK (length(trim(reviewer)) > 0),
    supersedes_id uuid REFERENCES source_baseline(id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE UNIQUE INDEX baseline_superseded_once
    ON source_baseline(supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE TABLE extraction_version (
    id uuid PRIMARY KEY,
    sha256 text NOT NULL REFERENCES content_object(sha256),
    extractor text NOT NULL,
    text_sha256 text NOT NULL,
    readable boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (sha256, extractor)
);
CREATE TABLE verification_result (
    id uuid PRIMARY KEY,
    source_id text NOT NULL REFERENCES evidence_sources(id),
    attempt_id uuid NOT NULL REFERENCES fetch_attempt(id),
    baseline_id uuid REFERENCES source_baseline(id),
    state text NOT NULL CHECK (state IN ('matches', 'changed', 'unreachable')),
    reason text NOT NULL,
    comparison_readiness text NOT NULL CHECK (comparison_readiness IN ('ready', 'not_ready')),
    byte_match boolean,
    text_match boolean,
    passages jsonb NOT NULL,
    checked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (state <> 'matches' OR (baseline_id IS NOT NULL AND comparison_readiness = 'ready'))
);

CREATE TRIGGER fetch_attempt_immutable BEFORE UPDATE OR DELETE ON fetch_attempt
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER content_object_immutable BEFORE UPDATE OR DELETE ON content_object
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER source_baseline_immutable BEFORE UPDATE OR DELETE ON source_baseline
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER extraction_version_immutable BEFORE UPDATE OR DELETE ON extraction_version
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER verification_result_immutable BEFORE UPDATE OR DELETE ON verification_result
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
