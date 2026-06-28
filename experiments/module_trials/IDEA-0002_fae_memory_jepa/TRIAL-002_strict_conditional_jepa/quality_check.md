# TRIAL-002 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-004
decision: PASS_KEEP
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-004`: U=71.22, S=77.60, H=74.27, ZS=81.38, best_epoch=33.
- Trial-level decision recorded as `keep`.
- Attempt confirmation status: confirmed_H=pending, confirmation_status=needs_confirmation.
- Same-config confirmation evidence is mixed: ATTEMPT-003 reached H=73.81 and ATTEMPT-004 reached H=74.27.
- The planned 10-run tuning sweep is blocked until the owner accepts this variance or requests a new confirmation strategy.
- Promotion/tag remains blocked because active v2 comparison reference is unconfirmed: v2 best_observed_H=74.29 (unconfirmed), confirmed_H=pending.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-004` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-004:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-004:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-004:runner_console` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_KEEP for ATTEMPT-004 evidence; trial-level tuning/promotion gate remains blocked by mixed confirmation.
