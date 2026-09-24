-- Comparability: reviewed judgements about whether reports can be compared, and relations between
-- claims or reports. Every table is append-only; a later judgement supersedes an earlier one by
-- naming it. No existing table is altered. A reviewer and a reason are mandatory on every row.
CREATE TABLE comparison_set (
    id text PRIMARY KEY,
    definition_version text NOT NULL,
    comparison_key jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE comparison_membership (
    id uuid PRIMARY KEY,
    set_id text NOT NULL REFERENCES comparison_set(id),
    report_id text NOT NULL,
    assessment text NOT NULL CHECK (assessment IN ('comparable', 'not_comparable', 'unresolved')),
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    reviewer text NOT NULL CHECK (length(trim(reviewer)) > 0),
    supersedes_id uuid REFERENCES comparison_membership(id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE UNIQUE INDEX membership_superseded_once
    ON comparison_membership(supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE INDEX membership_by_set ON comparison_membership(set_id, report_id);
CREATE TABLE claim_relation (
    id uuid PRIMARY KEY,
    left_ref text NOT NULL,
    right_ref text NOT NULL,
    relation text NOT NULL
        CHECK (relation IN ('contradicts', 'revises', 'duplicates_origin', 'different_scope', 'supports')),
    rationale text NOT NULL CHECK (length(trim(rationale)) > 0),
    evidence_refs jsonb NOT NULL,
    reviewer text NOT NULL CHECK (length(trim(reviewer)) > 0),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TRIGGER comparison_set_immutable BEFORE UPDATE OR DELETE ON comparison_set
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER comparison_membership_immutable BEFORE UPDATE OR DELETE ON comparison_membership
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
CREATE TRIGGER claim_relation_immutable BEFORE UPDATE OR DELETE ON claim_relation
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
