-- Extend an already-imported oil fixture without rewriting retained review records.
-- On a fresh database the seed is still empty here; normal fixture import supplies these rows.
ALTER TABLE investigation_seed DISABLE TRIGGER seed_immutable;
UPDATE investigation_seed
SET payload = jsonb_set(
        jsonb_set(
            payload,
            '{pack,sources}',
            payload->'pack'->'sources' || '[{"id":"O-S11","title":"EIA: Strait of Malacca oil flows and destinations","publisher":"U.S. Energy Information Administration","published_on":"2026-03-03","language":"en","url":"https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/","locator":"Strait of Malacca section; Table 2 and Figure 3","excerpt":"China accounted for 48% of the import volumes passing through the strait in 1H25.","format":"HTML","origin_group":"eia-world-oil-chokepoints","checked_on":"2026-09-22","review_status":"government_analysis_read_via_web","rights":"U.S. government publication; short anchor and authored notes retained.","independence":"Same underlying EIA chokepoint analysis as O-S10, recorded separately for a precise locator; tanker-derived volumes are estimates."}]'::jsonb
        ),
        '{pack,claims}',
        payload->'pack'->'claims' || '[{"id":"O-C16","subject":"oil-malacca","predicate":"carried_flow_within","object":"oil-world","evidence_ids":["O-S11"],"kind":"estimated_flow","source_as_of":"2025-H1","valid_from":"2025-01-01","valid_to":"2025-06-30","recorded_on":"2026-09-22","statement":"EIA estimated total oil flows through the Strait of Malacca at 23.2 million b/d in the first half of 2025.","caveat":"A tanker-derived aggregate estimate outside the main observation window; it does not trace individual cargoes.","review_status":"manually_source_checked_candidate","ground_truth":false},{"id":"O-C17","subject":"oil-malacca","predicate":"served_import_market","object":"oil-china","evidence_ids":["O-S11"],"kind":"estimated_trade_share","source_as_of":"2025-H1","valid_from":"2025-01-01","valid_to":"2025-06-30","recorded_on":"2026-09-22","statement":"EIA estimated that China accounted for 48% of import volumes passing through the Strait of Malacca in the first half of 2025.","caveat":"An aggregate destination share; it does not mean every Chinese crude import used Malacca or identify a cargo, supplier, or refinery.","review_status":"manually_source_checked_candidate","ground_truth":false}]'::jsonb
    ),
    fingerprint = '6325c8f0bbf95104629448ab3bf9fdea5158e6070771c3e4facbf5d13334db55'
WHERE case_id = 'oil-system-2025q3-2026q2'
  AND NOT payload->'pack'->'sources' @> '[{"id":"O-S11"}]'::jsonb;
ALTER TABLE investigation_seed ENABLE TRIGGER seed_immutable;

INSERT INTO evidence_sources(id, payload, content_hash)
SELECT
    'O-S11',
    '{"id":"O-S11","title":"EIA: Strait of Malacca oil flows and destinations","publisher":"U.S. Energy Information Administration","published_on":"2026-03-03","language":"en","url":"https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/","locator":"Strait of Malacca section; Table 2 and Figure 3","excerpt":"China accounted for 48% of the import volumes passing through the strait in 1H25.","format":"HTML","origin_group":"eia-world-oil-chokepoints","checked_on":"2026-09-22","review_status":"government_analysis_read_via_web","rights":"U.S. government publication; short anchor and authored notes retained.","independence":"Same underlying EIA chokepoint analysis as O-S10, recorded separately for a precise locator; tanker-derived volumes are estimates."}'::jsonb,
    '07e44ec8887cd53983439dcafe88a093b338e895bdaec614487dbf50b3fa4b72'
WHERE EXISTS (
    SELECT 1 FROM investigation_seed WHERE case_id = 'oil-system-2025q3-2026q2'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO knowledge_assertions(id, case_id)
SELECT claim_id, 'oil-system-2025q3-2026q2'
FROM (VALUES ('O-C16'), ('O-C17')) AS additions(claim_id)
WHERE EXISTS (
    SELECT 1 FROM investigation_seed WHERE case_id = 'oil-system-2025q3-2026q2'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO knowledge_proposals
    (id, claim_id, base_revision, payload, author, reason, request_hash)
SELECT * FROM (VALUES
    (
        '2f0c1835-fc87-5e33-a8e4-6d8534330112'::uuid,
        'O-C16',
        0,
        '{"id":"O-C16","subject":"oil-malacca","predicate":"carried_flow_within","object":"oil-world","evidence_ids":["O-S11"],"kind":"estimated_flow","source_as_of":"2025-H1","valid_from":"2025-01-01","valid_to":"2025-06-30","recorded_on":"2026-09-22","statement":"EIA estimated total oil flows through the Strait of Malacca at 23.2 million b/d in the first half of 2025.","caveat":"A tanker-derived aggregate estimate outside the main observation window; it does not trace individual cargoes.","review_status":"manually_source_checked_candidate","ground_truth":false}'::jsonb,
        'Research fixture import',
        'Imported as a candidate; application review has not occurred.',
        '6325c8f0bbf95104629448ab3bf9fdea5158e6070771c3e4facbf5d13334db55'
    ),
    (
        '81d46dc4-d8cb-547d-8b0e-58eb543ee03c'::uuid,
        'O-C17',
        0,
        '{"id":"O-C17","subject":"oil-malacca","predicate":"served_import_market","object":"oil-china","evidence_ids":["O-S11"],"kind":"estimated_trade_share","source_as_of":"2025-H1","valid_from":"2025-01-01","valid_to":"2025-06-30","recorded_on":"2026-09-22","statement":"EIA estimated that China accounted for 48% of import volumes passing through the Strait of Malacca in the first half of 2025.","caveat":"An aggregate destination share; it does not mean every Chinese crude import used Malacca or identify a cargo, supplier, or refinery.","review_status":"manually_source_checked_candidate","ground_truth":false}'::jsonb,
        'Research fixture import',
        'Imported as a candidate; application review has not occurred.',
        '6325c8f0bbf95104629448ab3bf9fdea5158e6070771c3e4facbf5d13334db55'
    )
) AS additions(id, claim_id, base_revision, payload, author, reason, request_hash)
WHERE EXISTS (
    SELECT 1 FROM investigation_seed WHERE case_id = 'oil-system-2025q3-2026q2'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO knowledge_proposal_evidence(proposal_id, source_id)
SELECT * FROM (VALUES
    ('2f0c1835-fc87-5e33-a8e4-6d8534330112'::uuid, 'O-S11'),
    ('81d46dc4-d8cb-547d-8b0e-58eb543ee03c'::uuid, 'O-S11')
) AS additions(proposal_id, source_id)
WHERE EXISTS (
    SELECT 1 FROM investigation_seed WHERE case_id = 'oil-system-2025q3-2026q2'
)
ON CONFLICT (proposal_id, source_id) DO NOTHING;
