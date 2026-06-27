# ATTEMPT-011 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=70.76, S=77.54, H=74.00, ZS=81.19, best_epoch=42.
- Attempt decision recorded as `keep`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-011` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-011:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-011:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-011:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
