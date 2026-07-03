# Result Index

authority: derived_index_only
metric_source: server summaries, batch status files, events files, Warehouse run dirs
result_ref: FINAL_REPORT.md
work_items_ref: WORK_ITEMS.md
campaign_run_map_ref: campaign_run_map.md
formal_result_ref: experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-006/result.yaml

This file is only a pointer table. Source-backed metric facts are consolidated in
`FINAL_REPORT.md` and still require an explicitly declared repeat protocol before
any confirmed claim. Multi-seed score search is not strict reproduction.

## Derived Top Singles

| Rank | Source | Job | Name | H | U | S | Evidence state |
|---:|---|---|---|---:|---:|---:|---|
| 1 | `RUN-20260702-0002` | DR-035 | `direction_sample_h48_w0.525_a0.005` | 75.02 | 72.69 | 77.51 | best observed single |
| 2 | `RUN-20260702-0002` | DR-009 | `dr016_direction_sample_h48_w0.45_a0.003_r02` | 75.00 | 72.93 | 77.19 | supporting single |
| 3 | `RUN-20260702-0003` / `ATTEMPT-006` | TUNE-002 / DR-004 | `tune_direction_h48_w0.525_a0.003` | 74.75 | 72.90 | 76.69 | repeat candidate |
| - | `RUN-20260703-0001` | DR-002 | `dr035_direction_sample_h48_w0.525_a0.005_s7` | 74.39 | 71.49 | 77.54 | seed_sweep only; not confirmed |

## Routing

```text
repeat_first: RUN-20260702-0002 / DR-035, exact_repeat with source seed 5 still required
seed_sweep_completed: RUN-20260703-0001 / ATTEMPT-005, not confirmed
repeat_neighbors: ATTEMPT-006 / TUNE-002 / DR-004, ATTEMPT-006 / TUNE-004 / DR-006
innovation_probes: stop_no_gain
promotion: blocked
```
