-- One pilot corpus per database schema. Evidence and authored proposals are immutable.
CREATE TABLE investigation_seed (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    fingerprint text NOT NULL,
    payload jsonb NOT NULL,
    imported_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE evidence_sources (
    id text PRIMARY KEY,
    payload jsonb NOT NULL,
    content_hash text NOT NULL
);
CREATE TABLE knowledge_assertions (
    id text PRIMARY KEY,
    current_revision integer NOT NULL DEFAULT 0 CHECK (current_revision >= 0)
);
CREATE TABLE knowledge_proposals (
    id uuid PRIMARY KEY,
    claim_id text NOT NULL REFERENCES knowledge_assertions(id),
    base_revision integer NOT NULL CHECK (base_revision >= 0),
    payload jsonb NOT NULL,
    author text NOT NULL CHECK (length(trim(author)) > 0),
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    request_hash text NOT NULL,
    proposed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (payload->>'id' = claim_id),
    CHECK (jsonb_array_length(payload->'evidence_ids') > 0),
    CHECK ((payload->>'valid_from')::date <= (payload->>'valid_to')::date)
);
CREATE TABLE knowledge_proposal_evidence (
    proposal_id uuid NOT NULL REFERENCES knowledge_proposals(id),
    source_id text NOT NULL REFERENCES evidence_sources(id),
    PRIMARY KEY (proposal_id, source_id)
);
CREATE TABLE knowledge_decisions (
    proposal_id uuid PRIMARY KEY REFERENCES knowledge_proposals(id),
    request_id uuid UNIQUE NOT NULL,
    decision text NOT NULL CHECK (decision IN ('accept', 'reject')),
    reviewer text NOT NULL CHECK (length(trim(reviewer)) > 0),
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    request_hash text NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE knowledge_versions (
    claim_id text NOT NULL REFERENCES knowledge_assertions(id),
    revision integer NOT NULL CHECK (revision > 0),
    proposal_id uuid UNIQUE NOT NULL REFERENCES knowledge_decisions(proposal_id),
    payload jsonb NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (claim_id, revision),
    CHECK (payload->>'id' = claim_id),
    CHECK (payload->>'review_status' = 'accepted'),
    CHECK (payload->>'ground_truth' = 'false')
);
CREATE INDEX proposals_by_claim ON knowledge_proposals(claim_id, proposed_at);

CREATE FUNCTION prevent_history_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Evidence and review history are append-only';
END;
$$;
CREATE TRIGGER seed_immutable BEFORE UPDATE OR DELETE ON investigation_seed
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER evidence_immutable BEFORE UPDATE OR DELETE ON evidence_sources
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER proposal_immutable BEFORE UPDATE OR DELETE ON knowledge_proposals
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER proposal_evidence_immutable BEFORE UPDATE OR DELETE ON knowledge_proposal_evidence
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER decision_immutable BEFORE UPDATE OR DELETE ON knowledge_decisions
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER version_immutable BEFORE UPDATE OR DELETE ON knowledge_versions
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
