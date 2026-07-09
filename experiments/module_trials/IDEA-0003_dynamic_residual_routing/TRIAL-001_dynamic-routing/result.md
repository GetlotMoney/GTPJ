# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-017 | v5 | CUB | 5 | 73.00 | 77.36 | 75.11 | 82.12 | 48 | +0.57 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-017
evidence_level: valid_single_run
result_status: rerun
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
server_summary_csv_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv
server_summary_jsonl_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl
server_batch_status_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json
server_events_jsonl_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl
server_status_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json
server_plan_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json
```

## Decision

`rerun`

ATTEMPT-017 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
