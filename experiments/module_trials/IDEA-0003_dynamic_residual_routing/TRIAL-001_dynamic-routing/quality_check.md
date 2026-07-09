# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-017
decision: PASS_RERUN
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-017`: U=73.00, S=77.36, H=75.11, ZS=82.12, best_epoch=48.
- Trial-level decision recorded as `rerun`.
- Attempt confirmation status: confirmed_H=pending, confirmation_status=needs_confirmation.
- Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json` exists in Warehouse.
- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_RERUN.
