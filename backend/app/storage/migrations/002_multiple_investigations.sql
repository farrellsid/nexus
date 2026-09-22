ALTER TABLE investigation_seed DISABLE TRIGGER seed_immutable;
ALTER TABLE investigation_seed ADD COLUMN case_id text;
UPDATE investigation_seed SET case_id = payload->'pack'->>'case_id';
ALTER TABLE investigation_seed ALTER COLUMN case_id SET NOT NULL;
ALTER TABLE investigation_seed DROP CONSTRAINT investigation_seed_pkey;
ALTER TABLE investigation_seed DROP COLUMN singleton;
ALTER TABLE investigation_seed ADD PRIMARY KEY (case_id);
ALTER TABLE investigation_seed ENABLE TRIGGER seed_immutable;

ALTER TABLE knowledge_assertions ADD COLUMN case_id text;
UPDATE knowledge_assertions a
SET case_id = s.case_id
FROM investigation_seed s
WHERE s.payload->'pack'->'claims' @> jsonb_build_array(jsonb_build_object('id', a.id));
ALTER TABLE knowledge_assertions ALTER COLUMN case_id SET NOT NULL;
ALTER TABLE knowledge_assertions
    ADD CONSTRAINT knowledge_assertions_case_fk
    FOREIGN KEY (case_id) REFERENCES investigation_seed(case_id);
CREATE INDEX assertions_by_case ON knowledge_assertions(case_id, id);
