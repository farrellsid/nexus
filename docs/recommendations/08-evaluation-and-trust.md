# H. Evaluation and trust in model output

## Recommendation

Start with deterministic fixture, retrieval and answer-contract tests; no paid model is required.
Separate evidence retrieval, extraction correctness and answer support scores.
Treat existing acceptance answers as drafts of the oracle, not ground truth.
Schema, verbatim text and numeric checks are necessary gates but do not prove entailment.
Retain human approval for factual changes, entity merges, causal interpretations and scenarios.

### Executable evaluation design

Proposed future command: `.venv/Scripts/python -m nexus_eval --suite evals/industry-v1 --retriever structured_lexical --answerer deterministic`. This module/path does not exist; this is an implementation contract, not a command reported as executed.

Convert each of the 26 cases to a versioned record:

```text
case_id, pack_release_hash, question, answer_class=(supported|partial|unknown),
required_claim_version_refs[], required_measurement_version_refs[],
required_source_passage_refs[], required_qualifiers[], prohibited_assertions[],
expected_entity_ids[], expected_actions[], temporal_cutoff?, language,
oracle_review_status, split=(development|held_out)
```

Harness sequence: validate references and oracle coverage; call the retriever without exposing expected IDs/answer text; collect ranked records; run a deterministic answerer that fills structured facts/slots or abstains; validate its response contract; write results keyed by corpus/eval/retriever hashes. Model adapters later replace only the answerer/proposer. Do not score reproducing the already-displayed `expected_answer` as question answering.

| Case examples | Required test behavior |
|---|---|
| Q01 | Retrieve C07/08/09; never assign combined 80% individually |
| Q02/Q06 | Commercial path allowed; no same-lot inference or completed European delivery |
| Q05 | Needs earlier expectation source S02 plus first-production evidence; C05 alone is an incomplete oracle |
| Q07/Q10/Q12 | Explicit unknown/unavailable or correct record-time limitation; no invented figure, site or pre-import state |
| O-Q01 | Needs O-M01's earlier and later measurements plus O-C02; one claim alone lacks the baseline |
| O-Q12 | Needs O-M07 and dated supporting passages, not merely O-C23's September point |
| O-Q13 | Needs all four O-M11 country measurements; O-C26 covers only Iraq |
| O-Q14 | Reject direct comparison of unlike periods/units; no implicit demand=imports substitution |

An empty `claim_ids` array is not automatically a negative-retrieval oracle: some unknown answers still require retrieving evidence explaining the limitation. Store relevant context separately from facts permitted in the answer. Split paraphrases and multilingual questions by source/origin family to reduce leakage, and have a human review held-out variants. Start with the small fixed suite and report raw counts, not impressive-looking statistics with unsupported generalization.

### Deterministic proposal gates

1. Strict versioned schema, size bounds, finite decimal values, referential integrity, allowed enums, coordinate and date checks. Unknown fields and unresolved references fail.
2. `verbatim_excerpt` must occur as a contiguous substring of a retained extraction version with character/page/cell anchors. Record separately exact-byte, canonical-text and OCR-confirmed checks; normalization may change whitespace/Unicode presentation, never rewrite units or words. Preserve original text and normalization algorithm version.
3. Every asserted numeric value must map to an explicit numeric token/cell in the supporting span, with unit, sign, scale, entity/row, column/period and statistic checked. Calculated values instead reference approved input versions and an allowlisted formula from D. Numeric token presence alone is insufficient: the wrong country's number can be present in the same table.
4. Verify support metadata: forecast/plan/capacity vocabulary cannot be silently promoted to observed output; source vintage and valid period must align. Contradictory qualifiers produce a review block. General semantic entailment remains a human check; simple code cannot prove arbitrary prose.
5. Render only approved record references and validated slots. Reject model-issued arbitrary SQL, URLs to fetch without acquisition checks, filesystem actions and mutation requests. Retrieved instructions remain data.

Negative fixtures should include changed numeral, correct numeral/wrong row, different unit, missing negation, plan stated as actual, wrong period, shared-origin duplication, invalid route and prompt-injection text. They must be clearly synthetic and separate from real packs.

### Metrics and release gate

Retrieval: recall@k against reviewed relevant records, precision@k, first relevant rank/MRR, full-support coverage (all required records found), and wrong-period/epistemic contamination. Report supported, unknown and multilingual subsets separately. Answering: factual-slot accuracy, citation resolvability, prohibited-assertion count, qualifier retention and abstention correctness; evaluate free prose with human support review. “Number appears somewhere in excerpt” is not an accuracy metric.

Initial proposed release gate: all deterministic integrity/security negatives rejected, no prohibited assertions in the small oracle suite, all mandatory evidence returned for the release's supported tour questions; surface any failed case rather than average it away. These are targets, not measured results. Performance/quality claims require actual held-out runs; record latency and human review effort alongside accuracy.

Retrieval note assessment: defer vectors, but qualify “structured lookups are exact.” They are exact for known IDs; natural-language intent, aliases, missing entity links and period interpretation are not implemented exact retrieval. Start ID/alias/entity/measure lookup plus lexical passage search; then evaluate paraphrase misses. Embeddings can also rank short descriptions, so long documents are not a strict prerequisite; the case for adding them is measured benefit, not document length. No universal prohibition on shipping embeddings is technically necessary, but local regenerable caches are the best default here because version, licence, size and provider dependencies matter.

## Evidence from the repo

Read both acceptance files: 12 copper and 14 oil cases, all `authored_acceptance_case_not_executed`. `test_workbench.py` checks an unknown answer string; `Workbench.tsx` renders authored answers. That is UI/fixture validation, not execution of all question-answer cases. `contracts/openapi.json` has neighborhood lookup but no search/answer endpoint. File enumeration found no retrieval/acquisition implementation in `backend/app` or `scripts`. Source anchors such as O-S20 discuss global output while O-C26/O-M11 require a country table; excerpt completeness is an oracle prerequisite.

## Options considered

| Option | Assessment |
|---|---|
| LLM judge as the only oracle | Reject: cost and correlated errors; not deterministic |
| Exact expected-answer string match | Too brittle and risks memorizing curated answers |
| Structured support contract + retrieval metrics + human prose review | Recommended; works before any model purchase |

## Migration and compatibility impact

Keep the existing 26 acceptance records unchanged; new eval fixtures reference their IDs and immutable release hashes. No edits to the 44 claims or append-only histories. Findings create proposed corrections, not automatic acceptance. The additive generator cannot update questions alone, as migration 006 demonstrates; version evaluations independently of the legacy seed initially. Models run read-only and submit through the same review service if enabled later. Tests must not write to the production review database.

## Risks

Oracle answers contain unsupported detail or stale framing; good retrieval cannot fix missing evidence. Schema-only success can make a false claim look rigorous. Small corpora overfit easily; no paid-model quality ranking follows from this review.

## Effort

**M**, foundations A–D; I for reliable excerpts; can begin with schema/negative fixtures immediately after design approval.

## Decisions needed from the user

Approve deterministic retrieval/slot evaluation before any model integration, with human review retained for factual acceptance?

## Unverified or not checked

The evaluation suite was designed, not implemented or executed. Existing app tests were inspected, not rerun (some start servers/write databases). No retrieval or model accuracy is claimed.
