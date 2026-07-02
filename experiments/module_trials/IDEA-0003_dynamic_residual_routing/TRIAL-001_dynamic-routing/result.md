# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-004 | v5 | CUB | 5 | 72.69 | 77.51 | 75.02 | 82.04 | 48 | +0.48 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-004
evidence_level: valid_single_run
result_status: needs_confirmation
promotion_decision: blocked
confirmed_H: pending
confirmation_status: needs_confirmation
runtime_summary_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:summary
runtime_summary_jsonl_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:summary_jsonl
batch_status_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:batch_status
plan_json_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:plan
events_jsonl_artifact_id: runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:events
campaign_report: experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/FINAL_REPORT.md
```

## Decision

`keep`

ATTEMPT-004 DR-035 is recorded as the current best observed single with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because this result still needs min3 repeat, log audit, artifact checks, and direction-gate quality evidence.
