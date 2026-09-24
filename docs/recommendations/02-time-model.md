# B. Time model

## Recommendation

Use separate valid time, publication time and application record time.
Offer “Period described” and optional “Known to Nexus by” controls, not one ambiguous as-of slider.
Store temporal precision and interval meaning; unknown bounds are not proof of timeless validity.
Keep sparse points sparse; never interpolate or carry a value forward without an explicit display rule.
Treat historical publication reconstruction separately from actual application history.

### Proposed shape and query

Add to versioned claim/measurement projections: `valid_kind = instant | interval | unknown`, `valid_start`, `valid_end_exclusive`, `precision = day | week | month | quarter | half_year | year | fiscal_year | unknown`, `calendar_id`, `original_period_label`, `temporal_basis_source_version_id`, `statistic = snapshot | total | mean_rate | ratio | capacity | qualitative`, and `time_mapping_state`. For instant facts use `valid_at`, not an artificial interval. Every interpretation of a fiscal label needs its calendar definition and evidence.

Keep `published_at`/`published_precision` on source versions, `source_as_of_label` on claims, `retrieved_at` on fetch attempts, `recorded_at` on imported/proposed records, and `accepted_at` on accepted revisions. Unknown publication dates remain null. Retain fixture `recorded_on` as an asserted curation date, distinct from database import time. A `source_as_of` string such as “page checked 2026-09-22” is retrieval context, not valid time.

For accepted facts with `known_at=T`, select the highest accepted revision per claim with `recorded_at <= T`, **then** apply validity/period filters. Do not filter validity first and resurrect an older superseded version that happens to fit the requested period. No qualifying accepted revision means absent from accepted state, not fallback to today's seed. A separately labelled candidate view may expose proposals that existed by T and decisions made by T. Future retraction requires an appended withdrawal event, not deletion or retroactive rejection of an accepted version.

Recommended API: `GET /api/facts?valid_on=YYYY-MM-DD&known_at=UTC_TIMESTAMP&view=accepted`, with a separate period-overlap form `period_start/period_end`. Select unknown-validity records into an explicit “date unresolved” group, never silently match them to every date. A snapshot can be shown beside a selected period as “latest available before period end; dated X,” but does not assert inventory was constant across it.

An accepted revision timestamp is useful transaction-time metadata, but current `clock_timestamp()` defaults are generated before commit. Promise “recorded by” replay, not precise visibility at an arbitrary microsecond or actual commit-time reconstruction. If strict replay is needed, publish coherent release IDs with an ordered watermark and store that ID in tours/exports.

### Actual pack migration

| Records | Interpretation / migration |
|---|---|
| 31 claims with both validity bounds null | Leave unknown. Candidate temporal enrichment requires review, even where dates can be extracted from text |
| O-C02/03/07, O-C08, O-C10/12/16/17/25/26 | Reported periods; preserve existing inclusive end as legacy and propose half-open equivalent only in v2 |
| C05 | Text reports an event on 2025-12-29 but valid bounds are null; proposed event-date enrichment, not source publication date 2026-01-02 |
| O-C13 | Policy applies to October; decision publication in September; never show as observed October output |
| O-C23 | Stored 2026-09-05–11 validity conflicts with statement/metric snapshot semantics: proposed `valid_at=2026-09-11` |
| O-C24 | Equal bounds 2026-01-01 indicate a capacity snapshot, not an empty half-open interval |
| O-M01–03 | Quarterly mean-rate observations with estimate status |
| O-M04 | Annual, half-year and quarter averages overlap; separate points, no connected continuous series |
| O-M05 | Three different measure/period/status tuples; split into independent measurements |
| O-M06, O-M11 | `period` contains locations/countries; move these to entity/category keys; period comes from group context and requires reviewed mapping |
| O-M07/08 | Stock/capacity snapshots; O-M09 weekly utilization ratios needs precise period definition confirmed |
| O-M10 | Fiscal-year totals and partial-year provisional total; no annualization by default |

Timeline: snap to available period boundaries, label cadence, show gaps and the source vintage. A selected date with no supported measurement displays “No data for this period.” Forecasts occupy a distinct visual lane. Structural claims of unresolved validity may remain in contextual background only with an explicit unresolved-date label. Freshness uses a configured expected release cadence plus grace period, distinguished from missing observation dates; do not invent provider release guarantees.

## Evidence from the repo

Inspected `knowledge.py`, `evidence.py`, `review.py`, SQL migration 001 and OpenAPI: claim validity is nullable `date`; source-as-of and metric period are strings; review timestamps are timezone-aware database timestamps. `MetricPoint` has only period/value/status. A Python enumeration found 31 null intervals and 13 bounded intervals; 18 copper records dated 2026-09-15, 26 oil records dated 2026-09-22. There is no as-of endpoint in `contracts/openapi.json`. Copper Q12 explicitly requires distinguishing publication reconstruction from app knowledge.

## Options considered

| Option | Assessment |
|---|---|
| One global date + latest value | Hides differing periods/vintages and future knowledge |
| Full temporal database replacement | Unnecessary for 44 claims |
| Append-only versions plus explicit period schema | Recommended; current history is a useful base |

## Migration and compatibility impact

Use A's projection tables and v1 decoders; preserve all 44 claims' original date fields. Never rewrite historical accepted versions or infer that September import existed in June. A dedicated migration adds temporal fields/tables; the additive generator cannot revise existing records or schema_version. Seed stays unchanged until an explicit versioned import cutover. Append approved temporal corrections as new versions using existing conflict protection. Regression cases: no pre-import facts, revision changes valid period, unknown bounds, O-C23 stock instant, O-C24 equal bounds, overlapping O-M04 periods, and fiscal-year partial totals.

## Risks

False precision, stale-value carry-forward and retrospectively backdated knowledge. Publication-time filtering cannot recover overwritten web pages. A source's release date and data period may differ by months.

## Effort

**M**, depends on A; D defines statistic/period arithmetic; I supplies source vintages; F/H consume it.

## Decisions needed from the user

Use period selection by default, with historical “known to Nexus” replay as an advanced control?

## Unverified or not checked

No temporal query executed against the live database. Fiscal calendars, provider lags and the observation basis of O-M09 need source-level verification before activation; dates above describe stored records and proposed interpretations.
