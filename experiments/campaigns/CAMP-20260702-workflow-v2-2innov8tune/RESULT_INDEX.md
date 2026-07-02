# Result Index

authority: derived_index_only
metric_source: server summaries, batch status files, events files, Warehouse run dirs
result_ref: FINAL_REPORT.md

This file is only a pointer table. Source-backed metric facts are consolidated in
`FINAL_REPORT.md` and still require min3 repeat before any confirmed claim.

## Derived Top Singles

| Rank | Source | Job | Name | H | U | S | Evidence state |
|---:|---|---|---|---:|---:|---:|---|
| 1 | `RUN-20260702-0002` | DR-035 | `direction_sample_h48_w0.525_a0.005` | 75.02 | 72.69 | 77.51 | best observed single |
| 2 | `RUN-20260702-0002` | DR-009 | `dr016_direction_sample_h48_w0.45_a0.003_r02` | 75.00 | 72.93 | 77.19 | supporting single |
| 3 | `RUN-20260702-0003` | DR-004 | `tune_direction_h48_w0.525_a0.003` | 74.75 | 72.90 | 76.69 | repeat candidate |

## Routing

```text
repeat_first: RUN-20260702-0002 / DR-035
repeat_neighbors: RUN-20260702-0003 / DR-004, RUN-20260702-0003 / DR-006
innovation_probes: stop_no_gain
promotion: blocked
```
