# ATTEMPT-013 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.19, S=76.52, H=73.76, ZS=80.91, best_epoch=33.
- Attempt decision recorded as `reject`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-013` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-013:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-013:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-013:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
