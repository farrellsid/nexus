# Provider cross-check report

Generated 2026-09-24 07:02 UTC by `scripts/crosscheck.py`. Raw counts: 7 equal_at_pack_precision, 8 no_observation.

A cross-check is not a verdict on the pack. `equal_at_pack_precision` means the provider's own number, scaled exactly and rounded half-up to the pack's decimal places, equals the pack's value. It does not show the pack cited that provider. `differs` may be a different definition, month or vintage, and needs a person. `no_observation` means the provider does not (yet) publish that period.

| Measurement | Label | Pack | Provider (scaled) | Provider raw | Status | Note |
|---|---|---|---|---|---|---|
| O-M07:0 | week ending 2026-06-19 | 412.1 | 412.134 | 412134 MBBL | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 412.1 |
| O-M07:1 | week ending 2026-07-17 | 411.7 | 411.675 | 411675 MBBL | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 411.7 |
| O-M07:2 | week ending 2026-09-11 | 423.4 | 423.429 | 423429 MBBL | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 423.4 |
| O-M09:0 | week ending 2026-06-19 | 96.1 | 96.1 | 96.1 % | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 96.1 |
| O-M09:1 | week ending 2026-09-11 | 96.8 | 96.8 | 96.8 % | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 96.8 |
| O-M08:0 | 2025-01-01 | 18.4 | 18.423493 | 18423493 B/CD | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 18.4 |
| O-M08:1 | 2026-01-01 | 18.2 | 18.160493 | 18160493 B/CD | equal_at_pack_precision | provider rounded to 1 decimal place(s) is 18.2 |
| O-M11:0 vs JODI | Saudi Arabia | 5.97 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, ..., 2026-05, 2026-06, 2026-07 |
| O-M11:0 vs EIA international | Saudi Arabia | 5.97 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, 2026-03, 2026-04, 2026-05 |
| O-M11:1 vs JODI | Iraq | 3.86 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, ..., 2026-05, 2026-06, 2026-07 |
| O-M11:1 vs EIA international | Iraq | 3.86 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, 2026-03, 2026-04, 2026-05 |
| O-M11:2 vs JODI | Russia | 8.36 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, ..., 2026-05, 2026-06, 2026-07 |
| O-M11:2 vs EIA international | Russia | 8.36 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, 2026-03, 2026-04, 2026-05 |
| O-M11:3 vs JODI | Iran | 2.16 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, ..., 2026-05, 2026-06, 2026-07 |
| O-M11:3 vs EIA international | Iran | 2.16 | - | - | no_observation | the provider has no observation for 2026-08; it has: 2026-01, 2026-02, 2026-03, 2026-03, 2026-04, 2026-05 |

## Requests (keys redacted)

| Request | Outcome | Bytes | SHA-256 |
|---|---|---|---|
| EIA stocks | ok | 5255 | `1ef6f5b2ed14f6c0` |
| EIA utilization | ok | 5298 | `697647e507c51957` |
| EIA capacity | ok | 1131 | `80ce86b6c76da002` |
| EIA country production | ok | 7982 | `9f50805c2302a80f` |
| JODI primary 2026 | ok | 5542684 | `909a73300584b877` |
