-- Normalisation releases: a reviewed projection of terminology, time, sources, entities and
-- measurements beside the recorded claims. Every table is append-only, and no existing table
-- (including investigation_seed) is altered. A release is readable only after an accept decision.
CREATE TABLE vocabulary_release (
    version text PRIMARY KEY,
    content_hash text NOT NULL,
    definition jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE normalisation_release (
    id text PRIMARY KEY,
    vocabulary_version text NOT NULL REFERENCES vocabulary_release(version),
    content_hash text NOT NULL UNIQUE,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE normalisation_decision (
    release_id text PRIMARY KEY REFERENCES normalisation_release(id),
    decision text NOT NULL CHECK (decision IN ('accept', 'reject')),
    reviewer text NOT NULL CHECK (length(trim(reviewer)) > 0),
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE entity_registry (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    canonical_id text NOT NULL,
    name text NOT NULL,
    category text NOT NULL,
    subtype text NOT NULL,
    PRIMARY KEY (release_id, canonical_id)
);
CREATE TABLE entity_alias (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    case_id text NOT NULL,
    legacy_id text NOT NULL,
    canonical_id text NOT NULL,
    PRIMARY KEY (release_id, case_id, legacy_id),
    FOREIGN KEY (release_id, canonical_id) REFERENCES entity_registry(release_id, canonical_id)
);
CREATE TABLE claim_projection (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    claim_id text NOT NULL REFERENCES knowledge_assertions(id),
    case_id text NOT NULL,
    basis_proposal_id uuid NOT NULL REFERENCES knowledge_proposals(id),
    predicate text NOT NULL,
    epistemic_status text NOT NULL,
    content_type text NOT NULL,
    modality text NOT NULL,
    release_status text NOT NULL,
    qualifiers jsonb NOT NULL,
    valid_kind text NOT NULL,
    valid_start date,
    valid_end_exclusive date,
    valid_at date,
    precision text NOT NULL,
    temporal_label text,
    statistic text NOT NULL,
    time_state text NOT NULL,
    needs_semantic_review boolean NOT NULL,
    note text,
    PRIMARY KEY (release_id, claim_id)
);
CREATE TABLE source_classification (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    source_id text NOT NULL REFERENCES evidence_sources(id),
    case_id text NOT NULL,
    publisher_class text NOT NULL,
    document_class text NOT NULL,
    legacy_reported_method text,
    PRIMARY KEY (release_id, source_id)
);
CREATE TABLE measurement (
    release_id text NOT NULL REFERENCES normalisation_release(id),
    id text NOT NULL,
    case_id text NOT NULL,
    metric_id text NOT NULL,
    point_index integer NOT NULL CHECK (point_index >= 0),
    measure text NOT NULL,
    value_text text NOT NULL,
    entity text,
    original_label text NOT NULL,
    valid_kind text NOT NULL,
    valid_start date,
    valid_end_exclusive date,
    valid_at date,
    precision text NOT NULL,
    temporal_label text,
    statistic text NOT NULL,
    time_state text NOT NULL,
    epistemic_status text NOT NULL,
    release_status text NOT NULL,
    claim_ids text[] NOT NULL,
    note text,
    PRIMARY KEY (release_id, id)
);
CREATE INDEX measurement_by_entity ON measurement(release_id, entity);

CREATE TRIGGER vocabulary_release_immutable BEFORE UPDATE OR DELETE ON vocabulary_release
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER normalisation_release_immutable BEFORE UPDATE OR DELETE ON normalisation_release
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER normalisation_decision_immutable BEFORE UPDATE OR DELETE ON normalisation_decision
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER entity_registry_immutable BEFORE UPDATE OR DELETE ON entity_registry
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER entity_alias_immutable BEFORE UPDATE OR DELETE ON entity_alias
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER claim_projection_immutable BEFORE UPDATE OR DELETE ON claim_projection
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER source_classification_immutable BEFORE UPDATE OR DELETE ON source_classification
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER measurement_immutable BEFORE UPDATE OR DELETE ON measurement
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
