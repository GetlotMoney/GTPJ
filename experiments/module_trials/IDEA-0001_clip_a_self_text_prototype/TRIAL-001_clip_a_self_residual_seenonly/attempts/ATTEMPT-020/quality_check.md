# ATTEMPT-020 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.13, S=77.63, H=74.24, ZS=81.42, best_epoch=48.
- Attempt decision recorded as `keep`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-020` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-020:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-020:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-020:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
