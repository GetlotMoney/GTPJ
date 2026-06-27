# ATTEMPT-018 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.08, S=77.42, H=74.12, ZS=81.51, best_epoch=33.
- Attempt decision recorded as `keep`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-018` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-018:best` exists in Warehouse.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-018:full` exists in Warehouse.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-018:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
