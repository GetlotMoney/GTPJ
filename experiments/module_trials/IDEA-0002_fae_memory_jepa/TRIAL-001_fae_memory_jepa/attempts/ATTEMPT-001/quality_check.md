# ATTEMPT-001 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: not_applicable
```

## Findings

- Metrics parsed from the registered training log: U=70.32, S=77.68, H=73.82, ZS=81.39, best_epoch=34.
- Attempt decision recorded as `revise`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-001:attempt-001` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-001:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-001:attempt-001:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-001:attempt-001:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
