# TRIAL-001 Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-007 | v5 | CUB | 5 | 72.58 | 76.75 | 74.61 | 81.82 | min3_mean | +0.07 |

## Evidence

```text
trial_id: TRIAL-001
attempt_id: ATTEMPT-007
evidence_level: confirmation_grade
result_status: confirmed
promotion_decision: blocked
confirmed_H: 74.61
confirmation_status: confirmed
attempt007_warehouse_manifest_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-007:dr035-exact-repeat
```

## Decision

`keep`

ATTEMPT-007 is recorded as `confirmation_grade` with confirmed_H=74.61 and confirmation_status=confirmed. Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
