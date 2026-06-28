# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-001
decision: PASS_REVISE
promotion_decision: not_applicable
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-001`: U=70.32, S=77.68, H=73.82, ZS=81.39, best_epoch=34.
- Trial-level decision recorded as `revise`.
- Attempt confirmation status: confirmed_H=pending, confirmation_status=not_applicable.
- Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-001:attempt-001` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-001:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-001:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-001:attempt-001:runner_console` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_REVISE.
