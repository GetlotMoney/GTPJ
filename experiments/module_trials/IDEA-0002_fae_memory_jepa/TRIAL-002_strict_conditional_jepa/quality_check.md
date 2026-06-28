# TRIAL-002 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-005
decision: PASS_NOT_CONFIRMED
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-005`: U=71.69, S=76.01, H=73.79, ZS=81.32, best_epoch=43.
- Trial-level decision recorded as `not_confirmed`.
- Attempt confirmation status: confirmed_H=pending, confirmation_status=needs_confirmation.
- Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-005` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-005:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-005:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-005:runner_console` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_NOT_CONFIRMED.
