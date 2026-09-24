# D. Units and conversions

## Recommendation

Separate measure definition, unit, scale, statistic, material basis and period.
Preserve source values and unit strings; compute display conversions as traceable derivatives.
Start with exact scale changes within the same unit basis; block mass–volume conversion without applicable evidence.
Use decimal values and explicit rounding, never additional displayed precision.
Do not standardize every industrial measure to one universal unit.

### Registry and current mappings

`unit_definition(id, version, symbol, dimension, scale_numerator, scale_denominator, reference_unit_id, definition_source_id)`; `measure_definition(id, version, name, canonical_unit_id, statistic, material_basis, denominator_definition?, aggregation_rule)`.

| Existing group | Canonical representation proposed | Restriction |
|---|---|---|
| O-M01/02 | total-oil transit mean rate; `barrel_petroleum/day` | Chokepoint-scoped; do not sum overlapping routes |
| O-M03 | world total oil supply mean rate; `barrel_petroleum/day` | Exact liquids/product coverage requires source-definition review; do not rename it crude production |
| O-M04 | crude import mean rate; `barrel_petroleum/day` | Preserve differing averaging periods |
| O-M05 | separate crude production, crude+product exports, forecast production; same rate unit | Matching unit does not make measures comparable |
| O-M06 | transit mean rate by route and 2025-H1 | Category field is not time |
| O-M07 | commercial crude stocks excluding SPR; `barrel_petroleum` | Snapshot, never summed across weeks |
| O-M08 | operable atmospheric distillation capacity; `barrel_petroleum/calendar_day` | Separate measure from actual input rate; calendar-day denominator retained |
| O-M09 | refinery utilization; `ratio` with percent display | Denominator = operable capacity; preserve source definition |
| O-M10 | crude imports total; `tonne_metric` | Partial fiscal-year total remains partial; no barrel conversion |
| O-M11 | crude production mean rate by country; `barrel_petroleum/day` | Same month, different entities; no time-series interpolation |

The names above are **proposed internal codes**, not claimed standard identifiers. “Million” is a scale of 1,000,000; percent is scale 1/100. Oil throughput stays in petroleum barrels/day, mass totals in metric tonnes, inventory in barrels, capacity in its source-defined basis. Copper numeric claims embedded in prose need separate sourced measurement extraction before conversion; don't regex all numerals into facts. Tonnes of contained copper and tonnes of concentrate require different measure/material definitions.

### Conversion facts

`conversion_factor_version(id, from_unit, to_unit, factor_decimal, offset_decimal, material_or_grade_id, geography_scope?, valid_period, temperature_basis?, pressure_basis?, method, source_version_id, passage_id, uncertainty_kind?, lower?, upper?, review_version_ref, supersedes_id?)`.

Exact dimensional/scale definitions belong in the registry with a retrieved standards citation before implementation. Empirical factors such as barrels per tonne belong in reviewed evidence. `derived_measurement(id, input_version_ids, conversion_factor_version_ids, formula_id, result_decimal, rounding_policy_id, created_at)` records reproducibility. A generic crude factor does not become valid for an unidentified grade or national mixed import basket. No factor in the current packs establishes a permissible India/China conversion.

Do not use this review to insert an assumed universal barrels-per-tonne number. Direct/indirect factors must agree in dimensions and applicable scopes; disallow ambiguous chains, or require human selection with the result labelled estimated. Retain uncertainty assumptions; multiplying endpoints is not automatically a confidence interval.

Period normalization: totals can be aggregated only across disjoint, complete coverage with the same definitions; average rates require duration weighting and actual calendar day counts. Stocks use dated snapshots; utilization needs its numerator/denominator or explicitly justified weights, not an unweighted average. Never annualize five months silently or combine overlapping annual/half-year observations. Rates multiplied by duration produce a derived total, labelled as a calculation from the stated mean, not a new measured quantity.

Currency: keep `currency_code`, `nominal_or_real`, `price_base_period`, `valuation=FOB|CIF|other|unknown`, and trade period. FX conversions require source, currency pair, fixing date or averaging rule; inflation adjustment requires the named index/version. The current metric groups contain no currency series; O-S19's excerpt mentions monetary values but that is not an authorized normalized dataset. Defer FX implementation until needed.

## Evidence from the repo

Enumerated all 11 `briefing.metrics` groups. `MetricSeries.unit` is free text; `MetricPoint.value` is float and points lack stable IDs, entity IDs, individual source bindings and measure definitions. O-M05 itself warns it is not homogeneous; O-M10 forbids implicit tonne/barrel conversion. `knowledge.py`, the oil pack and O-Q14 establish these gaps. No conversion table appears in storage migrations or OpenAPI.

## Options considered

| Option | Assessment |
|---|---|
| Store everything as SI immediately | Obscures industry conventions; introduces unsupported mass/volume assumptions |
| Retain strings only | Safe for display but cannot validate arithmetic |
| Small versioned registry + evidence-backed conversion facts | Recommended; exact scale conversion first |

## Migration and compatibility impact

Create measurement projections keyed initially by `(pack_release_hash, metric_id, original_point_index)` and assign permanent measurement IDs on reviewed import. The index is a provenance pointer, not identity across future reordered releases. Copy original decimal lexemes using JSON decimal parsing; do not round-trip through float to invent precision. Group-level source IDs remain legacy context until point-level passages are reviewed. These changes do not modify the 44 claim versions. Link measurements to claim versions where genuinely supported; do not claim every metric point is covered by the one existing related claim. Dedicated migrations add these tables; the current additive generator cannot rewrite metric groups. Preserve A/B history and seed checks.

## Risks

Accurate arithmetic over mismatched definitions is still wrong. Unqualified “ton” is ambiguous. A display scale change may conceal source rounding. Unknown temperature/grade or denominator should block derived comparisons.

## Effort

**M**, depends on A/B; prerequisite to C and reliable F/H.

## Decisions needed from the user

Approve exact scale changes only at first, with cross-dimensional and monetary conversions deferred until sourced?

## Unverified or not checked

No conversion factors, standard unit identifiers, FX rates or calendar definitions were externally verified or installed. Registry names are proposals; activation requires retrieved definitions. The EIA FAQ URL checked during research concerned consumption, not mass/volume conversion, and was not used as evidence for a factor.
