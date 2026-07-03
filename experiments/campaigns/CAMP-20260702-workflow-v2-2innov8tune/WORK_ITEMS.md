# Work Items

This file maps owner-facing workflow items to runner-local jobs. Runner `DR-xxx`
ids and runner-local `attempt_id` values are batch-local execution ids; they are
not GitHub formal `ATTEMPT-xxx` records.

## Mapping

| Work item | Runner job | Runner-local attempt_id | Workstream | Source type | Framework / Config | Seed | H | U | S | ZS | Evidence state |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| INNOV-001 | DR-001 | ATTEMPT-001 | innovation_probe | existing_trial_switch_probe | local sample + direction sample, h48, local_weight=0.06, weight_s2v=0.50, anchor=0.003 | 5 | 73.62 | 68.98 | 78.92 | 81.96 | stop_no_gain |
| INNOV-002 | DR-002 | ATTEMPT-002 | innovation_probe | existing_trial_switch_probe | direction sample + PSE class, h48, weight_s2v=0.50, pse_outer_ratio=0.55, anchor=0.003 | 5 | 73.63 | 74.04 | 73.22 | 81.46 | stop_no_gain |
| TUNE-001 | DR-003 | ATTEMPT-003 | direction_tune | trial_internal_config_search | direction sample, h48, weight_s2v=0.475, anchor=0.003 | 5 | 74.59 | 72.53 | 76.78 | 81.65 | single_run_valid |
| TUNE-002 | DR-004 | ATTEMPT-004 | direction_tune | trial_internal_config_search | direction sample, h48, weight_s2v=0.525, anchor=0.003 | 5 | 74.75 | 72.90 | 76.69 | 81.96 | repeat_candidate |
| TUNE-003 | DR-005 | ATTEMPT-005 | direction_tune | trial_internal_config_search | direction sample, h48, weight_s2v=0.50, anchor=0.001 | 5 | 74.62 | 72.26 | 77.14 | 81.58 | single_run_valid |
| TUNE-004 | DR-006 | ATTEMPT-006 | direction_tune | trial_internal_config_search | direction sample, h48, weight_s2v=0.50, anchor=0.005 | 5 | 74.67 | 72.29 | 77.21 | 81.62 | repeat_candidate |
| TUNE-005 | DR-007 | ATTEMPT-007 | direction_tune | trial_internal_config_search | direction sample, h40, weight_s2v=0.50, anchor=0.003 | 5 | 74.59 | 71.93 | 77.45 | 81.63 | single_run_valid |
| TUNE-006 | DR-008 | ATTEMPT-008 | direction_tune | trial_internal_config_search | direction sample, h56, weight_s2v=0.50, anchor=0.003 | 5 | 74.14 | 71.72 | 76.72 | 81.35 | single_run_valid |
| TUNE-007 | DR-009 | ATTEMPT-009 | direction_tune | trial_internal_config_search | direction class, h48, weight_s2v=0.50, anchor=0.003 | 5 | 74.20 | 69.36 | 79.77 | 81.27 | single_run_valid |
| TUNE-008 | DR-010 | ATTEMPT-010 | direction_tune | trial_internal_config_search | direction sample, h48, weight_s2v=0.45, anchor=0.004 | 5 | 74.64 | 72.43 | 76.98 | 81.62 | backup_repeat_candidate |

## Interpretation

- `INNOV-*` items were not paper-derived full innovations. They were existing
  TRIAL-001 switch probes used to test workflow routing and quickly screen
  combinations.
- `TUNE-*` items are trial-internal direction-gate config searches.
- No work item is confirmed. Top candidates require exact-repeat first, then
  declared stability or ablation evidence before promotion.

## Authority

Metrics are derived from:

```text
lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260702-0003-mixed2innov8tune-2gpu/summary.csv
lab4090:/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/
```

