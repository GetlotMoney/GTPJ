# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-003 | v5 | CUB |  | 73.10 | 76.71 | 74.86 | 81.84 | 37 | +0.32 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-003
evidence_level: valid_single_run
result_status: needs_confirmation
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
runtime_summary_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:summary
runtime_summary_jsonl_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:summary_jsonl
batch_status_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:batch_status
plan_json_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:plan
events_jsonl_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260701-0010:events
```

## Decision

`keep`

ATTEMPT-003 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
