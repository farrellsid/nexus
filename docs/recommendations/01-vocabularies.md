# A. Controlled vocabularies and migration

## Recommendation

Use versioned Nexus vocabularies, with optional external crosswalks, not Wikidata as the storage schema.
Split `predicate`, `epistemic_status`, `content_type`, `modality` and editorial review state.
Keep every original claim ID, payload and review; normalize through an explicitly versioned projection first.
Do not auto-accept the projection as a factual correction.
Retain immutable internal entity IDs and resolve legacy IDs through aliases; do not rewrite history to re-ID entities.
Normalize metric observations alongside claims before building cross-industry comparisons.

### Proposed closed vocabulary v1

The predicates are exactly the distinct target predicates in the 44-row table below. Each gets a registry record `(code, version, definition, subject_categories, object_categories, required_qualifiers, deprecated_by)`. Packs declare a vocabulary version; unknown codes fail import, rather than becoming arbitrary new predicates.

`epistemic_status`: `observed`, `reported`, `estimated`, `inferred`, `forecast`, `scenario`, `unknown`. `observed` requires a directly evidenced measurement/observation record, not merely a government publisher. No existing claim is promoted to observed. A scenario additionally requires attribution and assumptions; a forecast requires issuer and target period.

`content_type`: `structure`, `operation`, `production_event`, `contract`, `transaction`, `logistics_event`, `transport`, `capability`, `process`, `flow`, `trade`, `processing`, `production`, `policy`, `share`, `stock`, `capacity`. These describe content independently of how it is known.

`modality`: `actual`, `planned`, `capability`, `generic`, `required`, `unknown`. An announced future production requirement is a reported policy decision, not actual production and not necessarily a forecast. Capabilities remain capabilities even under the generic predicate `produces`.

Source classification: separate `publisher_class = company | government_agency | intergovernmental_body | research_body | news_publisher | industry_association | other | unknown` and `document_class = participant_announcement | statistical_release | analysis | outlook | filing | product_reference | operations_profile | provider_update | other | unknown`. Classification is editorial metadata, not evidence of reliability. Preserve `origin_group` and add upstream-data lineage when known.

Retrieval attempts use `method = http | browser | api | local_import | unknown`, plus tool/version, timestamp and snapshot ID (I). Existing `*_read_via_web` labels become `legacy_reported_method=web_tool`, **method unknown**: they do not establish an actual browser or HTTP retrieval.

### All 44 claim mappings

These are proposals based on the complete stored statements, kinds and caveats, not new verification of the underlying events. Existing endpoints remain unchanged in the first projection. Qualifiers must be materialized before simplifying a material-specific predicate; where meaning cannot yet be represented, block semantic activation and retain legacy rendering. All 19 legacy kinds appear below.

| Claim | Old predicate / kind | New predicate | Epistemic | Content | Modality / retained qualifier |
|---|---|---|---|---|---|
| C01 | operates / reported_structure | operates | reported | structure | actual |
| C02 | part_of / reported_structure | part_of | reported | structure | actual |
| C03 | produce / reported_operation | produces | reported | operation | actual; copper-in-concentrate output |
| C04 | planned_feed_to / operating_plan | feeds_to | reported | operation | planned |
| C05 | produced / reported_event | produces | reported | production_event | actual; first production 2025-12-29 |
| C06 | produces_byproduct / reported_operation | produces | reported | operation | actual; product_role=byproduct |
| C07 | anode_offtake_with / reported_contract | offtake_agreement_with | reported | contract | actual; material=anodes; combined share, not individual 80% |
| C08 | anode_offtake_with / reported_contract | offtake_agreement_with | reported | contract | actual; material=anodes; same combined-share restriction |
| C09 | anode_offtake_with / reported_contract | offtake_agreement_with | reported | contract | actual; material=anodes; remaining 20%, three-year term reported |
| C10 | sold_anodes_to / reported_transaction | sold_to | reported | transaction | actual; material=anodes; no delivery inference |
| C11 | reported_delivered_to / reported_event | arrived_at | reported | logistics_event | actual; reported cargo location, not all anodes |
| C12 | planned_route_via / reported_plan | routes_via | reported | transport | planned |
| C13 | reported_arrived_at / reported_event | arrived_at | reported | logistics_event | actual; first shipment, Q1 2026 |
| C14 | produces / reported_capability | produces | reported | capability | capability |
| C15 | produces / reported_capability | produces | reported | capability | capability; from cathodes |
| C16 | wire_rod_contract_with / reported_contract | supply_agreement_with | reported | contract | actual; material=rod; European plants particularly |
| C17 | manufactures / reported_capability | produces | reported | capability | capability |
| C18 | generic_input_for / generic_process | input_for | reported | process | generic; not batch lineage |
| O-C01 | refined_into / generic_process | refined_into | reported | process | generic |
| O-C02 | carried_flow_within / estimated_flow | carries_flow_within | estimated | flow | actual; total oil; 2026-Q2 |
| O-C03 | carried_flow_within / estimated_flow | carries_flow_within | estimated | flow | actual; total oil; 2026-Q2 |
| O-C04 | bypasses / reported_capability | bypasses | reported | capability | capability |
| O-C05 | connects_to / reported_structure | connects_to | reported | structure | actual |
| O-C06 | bypasses / reported_capability | bypasses | reported | capability | capability |
| O-C07 | imports / reported_trade | imports | estimated | trade | actual; statement explicitly says estimated; retain pending re-review |
| O-C08 | consumes / official_statistic | processes | reported | processing | actual; above-designated-size enterprise scope; not consumption |
| O-C09 | located_in / reported_structure | located_in | reported | structure | actual; national system, not a facility |
| O-C10 | produces / reported_estimate | produces | estimated | production | actual |
| O-C11 | part_of_production_in / forecast_context | contributes_production_to | forecast | production | planned; attribution=EIA, target=2026 |
| O-C12 | exports / official_statistic | exports | reported | trade | actual; material scope is crude PLUS products; endpoint mismatch requires review |
| O-C13 | coordinates_production_policy_for / reported_decision | sets_production_requirement_for | reported | policy | required; seven participants, not all OPEC+; October target |
| O-C14 | uses / reported_rerouting | uses | reported | transport | actual; no quantified spare capacity |
| O-C15 | uses / reported_structure | uses | reported | structure | actual |
| O-C16 | carried_flow_within / estimated_flow | carries_flow_within | estimated | flow | actual; 2025-H1 |
| O-C17 | served_import_market / estimated_trade_share | serves_import_market | estimated | share | actual; denominator=import volumes passing Malacca |
| O-C18 | connected_route_with / reported_structure | connects_to | reported | structure | actual; compound canal/pipeline corridor, not one sea edge |
| O-C19 | alternative_to / reported_alternative_route | alternative_to | reported | transport | capability; no particular cargo |
| O-C20 | alternative_to / reported_alternative_route | alternative_to | reported | transport | capability |
| O-C21 | alternative_to / reported_alternative_route | alternative_to | reported | transport | capability |
| O-C22 | provides_alternative_supply_route_to / reported_infrastructure | supply_route_to | reported | transport | capability; crude, alternative to Malacca |
| O-C23 | held_commercial_stocks_of / official_statistic | holds_stocks_of | reported | stock | actual; excludes SPR; point-in-time, not weekly total |
| O-C24 | operates_refining_capacity_of / official_statistic | has_processing_capacity_for | reported | capacity | capability; operable atmospheric distillation, calendar-day basis |
| O-C25 | imports / official_statistic | imports | reported | trade | actual; provisional=true, not automatically estimated |
| O-C26 | produces / reported_estimate | produces | estimated | production | actual; issuer=IEA |

`provisional` belongs in a separate `release_status = provisional | final | revised | unspecified`. O-C25 and O-M10 currently classify this differently. Likewise, `C11/C13` need a shipment-scope qualifier: the material entity `anodes` is not itself a particular shipment. Do not manufacture a shipment identifier to resolve that gap.

### Source migration mapping

| Legacy review_status | Proposed class mapping for actual source IDs |
|---|---|
| primary_document_read_via_web | S01–S11 company / participant_announcement, except S03 company / filing; S12–S13 company / product_reference; S14 company / operations_profile; O-S01 government_agency / analysis; O-S02 government_agency / outlook |
| government_analysis_read_via_web | O-S05, O-S08–O-S13: government_agency / analysis |
| government_statistics_read_via_web | O-S07, O-S14–O-S18: government_agency / statistical_release |
| official_statistics_read_via_web | O-S06, O-S19: government_agency / statistical_release |
| provider_update_read_via_web | O-S03: intergovernmental_body / provider_update, organizational classification pending review |
| participant_announcement_read_via_web | O-S04: intergovernmental_body / participant_announcement |
| intergovernmental_analysis_read_via_web | O-S20: intergovernmental_body / analysis |

These are metadata-based proposals. Hosting S03 on an exchange does not change its publisher from Zijin. Do not globally map the ambiguous primary-document label to “primary evidence.”

Optional crosswalks, fetched for this review: [P361, part of](https://www.wikidata.org/wiki/Property:P361); [P1056, product or material produced](https://www.wikidata.org/wiki/Property:P1056); [P131, located in an administrative territorial entity](https://www.wikidata.org/wiki/Property:P131). P1056 is a related mapping, not equivalent to an individual production event or quantity. P131 fits country containment only; it is not a universal mapping for every use of `located_in`. Store `(external_uri, mapping_relation, rationale, checked_at)` and leave unmatched predicates Nexus-specific.

## Evidence from the repo

Read `backend/app/{knowledge,evidence,review,investigation}.py`, `storage/{reviews,database}.py`, migrations 001–006, the generator, and `contracts/openapi.json`. Enumerated both evidence packs with Python's `json` and `collections`: 43 entities, 44 claims, 34 sources, 32 predicates, 19 kinds, seven source statuses; all claims candidate/false. `ProposalRequest` cannot change predicate, kind, endpoints or source-as-of. `ReviewService.propose` explicitly preserves them. `Claim` has `extra=forbid`; adding fields to old JSON without a versioned decoder breaks validation.

The generator unconditionally indexes `previous['pack']['briefing']['metrics']`; copper's `seed_payload()` explicitly removes absent briefing. It is not currently a general copper migration tool. It also refuses metric/question-only changes with no new sources/claims; migration 006 documents that workaround. `ON CONFLICT DO NOTHING` needs a content-equality check in a future installer, not silent ID collision acceptance.

## Options considered

| Option | Assessment |
|---|---|
| Rewrite old claims in place | Reject: loses historical meaning and violates immutable review payloads |
| Add new IDs for all 44 claims | Unnecessary duplication; breaks reading-guide links and separates histories |
| Versioned projection, then reviewed semantic changes | Recommended: raw replay remains exact; normalization is explicit |
| Adopt an external ontology wholesale | Too much mismatch for contracts, estimates and aggregate flows |

## Migration and compatibility impact

1. Preserve a backup and old fixture/seed hashes. Keep v1 `Claim` decoding for existing proposal/version payloads and retain all old API IDs. Do not disable history triggers.
2. Add immutable `vocabulary_release(version, definition_hash, created_at)` and `claim_projection(id, claim_id, basis_payload_hash, basis_proposal_id?, basis_revision?, vocabulary_version, predicate, epistemic_status, content_type, modality, qualifiers_json, mapping_state, supersedes_id?, recorded_at)`. Enforce exactly one basis type and FK to the original proposal/version where applicable. Projection approval is separate from claim acceptance.
3. Project each **actual accepted version** and retained candidate from its own payload; do not overlay fixture text onto locally corrected statements/dates. Use an explicit mapping rule ID; ambiguous revisions enter review. The 44-row table covers fixtures, not every possible local correction.
4. Add entity aliases `(namespace, old_id, canonical_entity_id)` without changing historical endpoints. External QIDs are optional, versioned links with merge/split history, not primary keys.
5. Keep fixtures unchanged initially. A dedicated schema migration adds projection tables; the additive generator continues serving legacy additions unchanged. A future v2 importer uses parameterized data statements and immutable `pack_release` records; it must not execute pack-supplied SQL. Retain legacy seed comparison for legacy packs and introduce an explicit v2 release manifest check, rather than bypassing fingerprint validation.
6. Expand the review command contract for semantic changes. Acceptance writes new versions atomically with the same head lock, expected revision and idempotency protections. O-C08/O-C12/O-C13 and C11/C13 deserve explicit semantic review. Regenerate OpenAPI/types only during authorized implementation. Test upgrade and clean install, old history decoding, stale proposals, ID collisions, rollback and identical raw-history hashes.

For semiconductors, reuse structure/production/contracts/trade; add controlled material, process-stage and measure definitions through a reviewed vocabulary release. Do not create `wafer_contract_with`, `chip_contract_with`, etc. A pack may request new vocabulary, not execute extensions or silently register codes. Compound assertions should split into linked child claims prospectively; old statements and their supersession links remain readable.

## Risks

Semantic compression can erase plans, capacities, product forms and cargo scope. A crosswalk is not identity proof. A classification inferred from metadata must not upgrade evidence quality. Existing local reviews were not queried; the migration must handle revisions beyond these fixtures.

## Effort

**L** for safe migration and versioned contracts; **S** for reviewing this mapping. Foundational for B–D, F and H; I supplies trustworthy source versions.

## Decisions needed from the user

Approve the projection-first approach and keep historical IDs resolvable? Approve Nexus-owned vocabularies with optional external mappings?

## Unverified or not checked

No migration executed and no live review database queried. Mapping is proposed, not accepted. Underlying physical events and the publisher classification of JODI were not independently established. Only the three listed Wikidata property definitions were fetched; no additional property IDs are asserted.
