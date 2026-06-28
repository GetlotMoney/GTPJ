# ATTEMPT-004 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.22, S=77.60, H=74.27, ZS=81.38, best_epoch=33.
- Attempt decision recorded as `keep`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-004` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-004:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-004:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-004:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
