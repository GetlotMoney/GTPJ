# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-007
decision: PASS_KEEP
promotion_decision: blocked
evidence_level: confirmation_grade
```

## Findings

- Metrics are synchronized from `ATTEMPT-007`: U=72.58, S=76.75, H=74.61, ZS=81.82, best_epoch=min3_mean.
- Trial-level decision recorded as `keep`.
- Attempt confirmation status: confirmed_H=74.61, confirmation_status=confirmed.
- Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-007:dr035-exact-repeat` exists in Warehouse.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_KEEP.
