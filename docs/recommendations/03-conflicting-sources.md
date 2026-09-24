# C. Conflicting sources

## Recommendation

Keep every sourced assertion; disagreement is a relationship between versions, not a replacement value.
Show reports side by side by default.
Offer a labelled “range of comparable reports” only after explicit comparability review.
Never call min–max a confidence interval, average silently, or include an old revision as another independent report.
Separate semantic disagreement, non-comparability, revision and shared-source duplication.

### Proposed data model

`measurement_version(id, claim_version_ref, entity_id, measure_definition_id, material_scope_id, geography_scope_id, population_scope_id, statistic, period_id, unit_id, value_decimal, release_status, epistemic_status, source_version_id, origin_group, supersedes_measurement_id?, recorded_at)`.

`comparison_set(id, definition_version, comparison_key_json, created_at)`; append-only `comparison_membership(id, set_id, measurement_version_id, assessment= comparable | not_comparable | unresolved, reason, reviewer, recorded_at, supersedes_id?)`; append-only `claim_relation(id, left_version_ref, right_version_ref, relation= contradicts | revises | duplicates_origin | different_scope | supports, rationale, evidence_refs, reviewer, recorded_at)` for numeric and nonnumeric claims alike.

Compare only when entity, material/grade, geography, population, definition, statistic, complete period, denominator (for shares), seasonal adjustment, valuation basis (if monetary), epistemic class and relevant methodology are compatible. Units must match or have an approved D conversion chain. Missing metadata means unresolved, not wildcard equality. Same measure label is insufficient. Vintage compatibility is a deliberate reviewer judgment: newer publication alone neither establishes nor disproves conflict.

Within an issuer's series, resolve explicit revision lineage at the selected B record cutoff. Do not assume two releases with similar titles revise each other; require a series/period identifier and documented relationship. Shared upstream data can be retained as separate attributions but must not count as independent corroboration. Derive ranges only from the active comparable set at a chosen release/cutoff and record member version IDs, conversion IDs and calculation version. Never persist an unexplained synthetic “consensus claim.”

### Display

| Situation | Display |
|---|---|
| Two approved comparable numbers | Both source-labelled points plus optional min–max bracket, “range of N reports; not a confidence interval” |
| Different scope, unit basis, period or methodology | Side-by-side cards with the difference stated; no combined range |
| Same source revision | Latest eligible value; “revised from …” history, not a conflict badge |
| Nonnumeric disagreement | Attributed propositions and supporting passages; explicit unresolved/curator assessment |
| One number, no comparator | One reported estimate and its caveats, never a fabricated uncertainty band |
| Forecast versus reported production | Separate lanes; no common range |

The present packs do not supply an actual two-source same-measure conflict set. Use clearly synthetic differing-report fixtures for implementation tests; do not manufacture an OPEC comparator for O-M11 from its caveat.

## Evidence from the repo

`knowledge.py` has statements and metric floats but no numeric assertion model, comparability keys or disagreement relations. `review.py` revises one claim rather than linking competing claims. Oil O-M05 explicitly mixes production, exports and a forecast; O-M06 values overlap routes; O-M11's caveat mentions other methodologies but contains only IEA values. O-Q14 refuses direct India/China comparison. Copper sources have shared `origin_group`/independence notes. These were read in the two packs and acceptance-case files.

## Options considered

| Option | Assessment |
|---|---|
| Automatic min–max for matching titles | Reject: definitions and scopes differ |
| Choose one “best” provider | Possible curated preference, but must preserve and show alternatives |
| Reviewed comparability + attributed reports | Recommended; useful ranges without hiding disagreements |

## Migration and compatibility impact

A/B/D define the required measurement version shape. Append tables and links; no changes to 44 retained claims or append-only proposal/decision/version rows. Initially every numeric comparison is unresolved until audited. Imported competing reports get distinct logical claim IDs; same-series revisions append to the appropriate lineage after review. The additive generator can add new legacy claims, but cannot implement this model or correct existing metrics: use dedicated migrations and A's release import path. No seed rewrite disguised as a conflict merge. Tests must cover mismatched scope, known conversions, absent metadata, same-origin duplicates and revision cutoffs.

## Risks

Ranges can falsely suggest probabilistic uncertainty or independence. Comparability rules may become overly permissive under pressure to populate a chart. Even identical definitions do not establish equal source credibility.

## Effort

**M**, after A/B/D; source-version lineage from I. F uses reviewed sets only.

## Decisions needed from the user

Approve side-by-side reports as the default and ranges only after explicit comparability review?

## Unverified or not checked

No real conflict adjudicated. No confidence intervals or alternative provider values fetched. The recommendations describe semantics and actual schema gaps, not evidence that today's stored figures conflict.
