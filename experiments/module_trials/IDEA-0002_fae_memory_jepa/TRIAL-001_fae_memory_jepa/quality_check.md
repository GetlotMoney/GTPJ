# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-002
decision: PASS_KEEP
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-002`: U=71.15, S=77.11, H=74.01, ZS=81.31, best_epoch=33.
- Trial-level decision recorded as `keep`.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-001:attempt-002` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-002:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-002:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-001:attempt-002:runner_console` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_KEEP.
