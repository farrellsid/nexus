# Evaluation oracle review (roadmap M3, [A] and [U])

Written 2026-09-24 by the assistant. **Every expected answer below is a draft, not ground truth,
until you confirm it.** The evaluation suite is `evals/industry-v1/suite.json` (26 cases; all
`assistant_draft`). No model is involved: the harness is deterministic and needs no network.

Run it from `backend/` with `PYTHONPATH=.`:

```
python ../scripts/evaluate.py check
python ../scripts/evaluate.py run --k 10
python ../scripts/evaluate.py oracle
```

## What was checked, and how

- For every case I read the stored expected answer, the claims it cites, their caveats and their retained excerpts, straight from the packs.
- `evaluate.py oracle` adds a mechanical check: figures in the expected answer must appear in the records the case requires, and each required record's own figures must appear in the sources it cites. A finding is a prompt, not proof.
- Things figures cannot catch (a claim of "lower", an unnamed source) I found by reading. Where I named a source or origin group I verified it in the pack.
- Limits: the corpus is the fixture packs. Corrections that the review layer accepts later live in the database and are not in it, so the 13 pending M0 proposals do not yet change anything here. Events (for example O-E05) are not in the corpus.

## Retrieval and baseline results (raw counts)

The retriever is BM25 plus a canonical-entity boost. It sees only the question. The baseline answerer always abstains. Not a quality claim: 26 cases, all in the development split, tuned by nobody.

```
retrieval at k=10; baseline = always abstain

case   class     facts  full  rank  sources  baseline
Q01    supported 2/3    False 2     1/2      6 violation(s)
Q02    partial   1/3    False 2     0/2      5 violation(s)
Q03    unknown   0/0    True  -     0/0      pass
Q04    partial   1/1    True  2     0/2      3 violation(s)
Q05    partial   1/1    True  1     1/2      3 violation(s)
Q06    supported 1/4    False 1     1/2      7 violation(s)
Q07    unknown   0/0    True  -     0/0      pass
Q08    supported 0/1    False 1     1/2      3 violation(s)
Q09    supported 2/4    False 1     2/3      6 violation(s)
Q10    unknown   0/0    True  -     0/0      pass
Q11    supported 3/3    True  1     1/2      5 violation(s)
Q12    unknown   0/0    True  -     0/0      2 violation(s)
O-Q01  supported 3/3    True  2     1/1      5 violation(s)
O-Q02  partial   2/4    False 4     0/1      6 violation(s)
O-Q03  partial   3/3    True  1     1/1      5 violation(s)
O-Q04  partial   2/2    True  2     1/1      4 violation(s)
O-Q05  partial   3/4    False 1     0/2      6 violation(s)
O-Q06  partial   3/6    False 3     0/2      8 violation(s)
O-Q07  unknown   0/0    True  -     0/0      pass
O-Q08  unknown   0/0    True  -     0/0      pass
O-Q09  unknown   0/0    True  -     0/0      pass
O-Q10  partial   0/4    False -     0/0      6 violation(s)
O-Q11  supported 3/4    False 1     1/2      6 violation(s)
O-Q12  partial   4/4    True  1     0/3      6 violation(s)
O-Q13  supported 5/5    True  1     1/1      7 violation(s)
O-Q14  unknown   0/0    True  -     0/0      1 violation(s)

full support: 8 of 18 cases that need facts
baseline meets the contract: 6 of 26 cases
  Q01 missing claim:C09
  Q02 missing claim:C10, claim:C16
  Q06 missing claim:C11, claim:C12, claim:C13
  Q08 missing claim:C10
  Q09 missing claim:C05, claim:C14
  O-Q02 missing claim:O-C02, measurement:oil-system-2025q3-2026q2:O-M01:3
  O-Q05 missing claim:O-C08
  O-Q06 missing claim:O-C10, claim:O-C11, claim:O-C12
  O-Q10 missing claim:O-C02, claim:O-C07, claim:O-C10, claim:O-C13
  O-Q11 missing claim:O-C19
```

Reading it: full support (every required claim and measurement in the top 10) holds for 8 of the 18 cases that need facts. The baseline meets the contract only on the unknown cases that require no stated limitation. Q12 and O-Q14 need a stated limitation, which a silent abstention does not give. These are the numbers a later retriever or model must beat, measured on the same suite.

## Mechanical oracle findings

```
case Q01: claim:C09 figure 20 is not in its cited sources
case O-Q01: claim:O-C02 figure 4.9 is not in its cited sources
case O-Q01: measurement:oil-system-2025q3-2026q2:O-M01:1 figure 21.6 is not in its cited sources
case O-Q01: measurement:oil-system-2025q3-2026q2:O-M01:3 figure 4.9 is not in its cited sources
case O-Q02: claim:O-C02 figure 4.9 is not in its cited sources
case O-Q02: claim:O-C03 figure 8.1 is not in its cited sources
case O-Q02: measurement:oil-system-2025q3-2026q2:O-M01:3 figure 4.9 is not in its cited sources
case O-Q02: measurement:oil-system-2025q3-2026q2:O-M02:3 figure 8.1 is not in its cited sources
case O-Q06: claim:O-C10 figure 13.8 is not in its cited sources
case O-Q06: measurement:oil-system-2025q3-2026q2:O-M05:2 figure 13.8 is not in its cited sources
case O-Q10: claim:O-C02 figure 4.9 is not in its cited sources
case O-Q10: claim:O-C10 figure 13.8 is not in its cited sources
case O-Q12: expected answer figure 7 is not in any required or context record
case O-Q13: claim:O-C26 figure 3.86 is not in its cited sources
case O-Q13: measurement:oil-system-2025q3-2026q2:O-M11:0 figure 5.97 is not in its cited sources
case O-Q13: measurement:oil-system-2025q3-2026q2:O-M11:1 figure 3.86 is not in its cited sources
case O-Q13: measurement:oil-system-2025q3-2026q2:O-M11:2 figure 8.36 is not in its cited sources
case O-Q13: measurement:oil-system-2025q3-2026q2:O-M11:3 figure 2.16 is not in its cited sources

18 finding(s) across 26 cases (prompts for review, not proof)
```

## The 26 expected answers

`Agree` means the stored answer is supported by the retained evidence as far as I could check. It is not physical verification and not a domain judgement; that is yours.

| Case | Class | Verdict | Note |
|---|---|---|---|
| Q01 | supported | Agree, with a finding | The 80% is anchored (S01, "combined 80%"). The 20% for Trafigura Asia (C09) is not: S04's retained excerpt is only "with Trafigura Asia Trading Pte Ltd." |
| Q02 | partial | Agree | Relationships are disclosed; no same-lot evidence. |
| Q03 | unknown | Agree | Europe is stated; no refinery is named. |
| Q04 | partial | Agree | A denial of an unsupported conclusion; C02 says Kakula is a mine within the complex. |
| Q05 | partial | **Disagree: proposed correction** | The stored answer never answers "was the smelter operating in October 2025". See F1. |
| Q06 | supported | Agree | February: cargo at Kolwezi, rail planned; Q1 2026: first shipment reached Lobito; April: European arrival still expected (May). |
| Q07 | unknown | Agree | The question's premise ("output was lost") has no support. |
| Q08 | supported | Agree, verified | S06 and S07 share origin group `kamoa-aurubis-joint-2026-02`. |
| Q09 | supported | Agree | Anodes (C05) versus cathodes and rod (C14, C15, C18). |
| Q10 | unknown | Agree | No validated identity or geocoding. |
| Q11 | supported | Agree | Contracts (C07, C08) and production (C05) are separate states. |
| Q12 | unknown | Agree | Class unknown, but the limitation must be stated: publication-time reconstruction only, recorded September 2026. |
| O-Q01 | supported | Agree, with a finding | The answer's 21.6 (2025-Q4) is not in claim O-C02; it needs metric O-M01. Both values are anchored only by the replacement excerpt O-S21. See F3. |
| O-Q02 | partial | Agree | "Unknown" plus two quarterly estimates. Same anchoring finding as O-Q01. |
| O-Q03 | partial | Agree | Capacity is not throughput. |
| O-Q04 | partial | Agree | Capability, not actual flow or spare capacity. |
| O-Q05 | partial | **Flag** | "China NBS reported lower June refinery processing": nothing in the pack says "lower". See F2. |
| O-Q06 | partial | Agree, with a finding | The 13.8 million b/d forecast is in no retained excerpt. See F4. |
| O-Q07 | unknown | Agree | A decision is not measured output. |
| O-Q08 | unknown | **Flag** | "The sources describe several contributing conditions" is not anchored. See F5. |
| O-Q09 | unknown | Agree | Country-level data cannot identify a refinery. |
| O-Q10 | partial | Agree, with a note | "June 2026 is the latest common endpoint" comes from the oil README and metric periods, not from any claim. |
| O-Q11 | supported | Agree | Alternatives are identified; capacity and use are not established. |
| O-Q12 | partial | **Flag** | The 7% below (June 19) is in no retained excerpt. The 6% is in O-S16 and the 1% in O-S14. See F6. |
| O-Q13 | supported | **Flag** | Russia 8.36, Saudi Arabia 5.97 and Iran 2.16 are unanchored. See F7. |
| O-Q14 | unknown | Agree | Unlike units and periods; imports are also not demand. |

## Findings

**F1. Q05's expected answer does not answer the question.** Stored: "June's October expectation is a forecast. First anodes were later reported for December 29." Proposed replacement: "Not established. The corpus has no evidence of anode production in October 2025. Ivanhoe's western Kakula restart release (S02) only expected the first anode in October 2025, which is a forecast, and first anodes were reported produced on 2025-12-29 (C05)." Note that S02 is cited by C02 but not by C05.

**F2. O-Q05 says "lower" without a comparison.** O-C08 and its excerpt give 51.24 million tonnes for June 2026 and nothing to compare it with. Proposed: drop "lower", or add a sourced prior-month or prior-year figure first.

**F3. O-C02 and metric O-M01 cite O-S01, whose retained excerpt is only the AIS caveat.** The 4.9 and 21.6 values are in the M0 replacement O-S21, but neither the claim nor the metric group cites it until the M0 proposals are accepted and M4 binds points to passages. Nothing is wrong with the values; the anchor is.

**F4. The 13.8 million b/d full-year forecast (O-M05, O-C10 caveat) is in no retained excerpt.** O-S26 anchors only the 13.7 first-half figure.

**F5. O-Q08's "several contributing conditions" is unanchored.** The only Brent records are event O-E05 (August average $91 per barrel) and source O-S02, which is script-rendered and unreadable to a plain fetch. Events are not yet in the evaluation corpus.

**F6. O-Q12's 7% is unanchored.** O-S15's excerpt gives 412.1 million barrels for the week ending June 19 without the percentage. Proposed: retain the passage that states it, or drop the 7% from the expected answer.

**F7. Three of the four O-M11 values are unanchored.** The retained excerpts (O-S20 and its replacement O-S23) stop at the Iraq row. This is the same class of defect as O-C26 in M0, one level down: the metric points are not tied to passages.

**F8. Copper C09's 20% is unanchored** (see Q01). Together with C11 and C13 (found in M2) this is a pattern in the copper pack: short mid-sentence excerpts that do not state the claim. It belongs to the deferred copper audit.

F3 to F8 are one defect class: **a value is stored, the page probably supports it, but no retained passage shows it.** M4's point-level passages are the fix. The harness will show them shrink as they are repaired.

## Comparability, in one paragraph

`app/comparability` groups candidate reports (same entity, measure, statistic, unit and period, at least two origin groups), and builds side-by-side cards. A range appears only when at least two independent reports are marked `comparable` by a reviewer, share a lane and unit, and have their scope metadata (geography, population, methodology, seasonal adjustment) recorded. The packs hold none of that metadata and no second-source conflict, so on real data every report starts unresolved and no range can appear; the behaviour is proven on synthetic reports only. Reviewer and reason are mandatory on every judgement, and no write endpoint exists yet.

## Decisions for you (roadmap M3 [U])

1. **Confirm each expected answer** in the table above, or tell me which to change. For the rows marked Flag or Disagree, choose: accept my proposed correction, drop the unanchored detail, or keep it and wait for a source.
2. **Confirm the class of each case** (supported, partial, unknown). The classes decide whether an honest answer may abstain.
3. **Approve the comparability rules**, in particular that a range needs a reviewer's `comparable` mark, independent origins and recorded scope metadata.
4. **Confirm that you are the only reviewer** who marks reports comparable for now. Reviewer names are stored on every judgement.
