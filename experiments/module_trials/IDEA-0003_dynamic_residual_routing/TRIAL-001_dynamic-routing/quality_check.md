# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-003
decision: PASS_KEEP
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-003`: U=73.10, S=76.71, H=74.86, ZS=81.84, best_epoch=37.
- Trial-level decision recorded as `keep`.
- Attempt confirmation status: confirmed_H=pending, confirmation_status=needs_confirmation.
- Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:summary` exists in Warehouse.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:summary_jsonl` exists in Warehouse.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:batch_status` exists in Warehouse.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:plan` exists in Warehouse.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:events` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_KEEP.
