-- Measurement-level source bindings: sources whose data was checked against a specific metric
-- point, in addition to the sources of its metric group, with the reason for the binding.
-- Append-only like every normalisation table; earlier releases simply have no rows here.
CREATE TABLE measurement_source (
    release_id text NOT NULL,
    measurement_id text NOT NULL,
    source_id text NOT NULL REFERENCES evidence_sources(id),
    basis text NOT NULL CHECK (length(trim(basis)) > 0),
    PRIMARY KEY (release_id, measurement_id, source_id),
    FOREIGN KEY (release_id, measurement_id) REFERENCES measurement(release_id, id)
);

CREATE TRIGGER measurement_source_immutable BEFORE UPDATE OR DELETE ON measurement_source
FOR EACH ROW EXECUTE FUNCTION prevent_history_rewrite();
