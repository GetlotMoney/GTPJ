# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-003
decision: PASS_KEEP
promotion_decision: blocked
evidence_level: confirmation_grade
```

## Findings

- Metrics are synchronized from `ATTEMPT-003`: U=71.32, S=77.40, H=74.24, ZS=81.62, best_epoch=33.
- Trial-level decision recorded as `keep`.
- Clean confirmation passed for the 74-level ATTEMPT-002 result.
- Promotion/tag remains blocked because the active v2 comparison reference is unconfirmed:
  `best_observed_H=74.29`, `confirmed_H=pending`; ATTEMPT-003 is 0.05 below that unconfirmed reference.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-001:attempt-003` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-003:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-003:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-001:attempt-003:runner_console` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_KEEP. No formal mainline tag is allowed from this evidence because the promotion gate is blocked and the v2 reference has not been clean-confirmed.
