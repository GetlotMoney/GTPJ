# ATTEMPT-002 Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U=71.32, S=77.40, H=74.24, ZS=81.62, best_epoch=33.
- Attempt decision recorded as `keep`.
- Evidence level is `confirmation_grade`: this is a clean rerun of the byte-identical ATTEMPT-001 config and confirms the strict conditional path at the 74-level.
- This is migrated historical evidence: the original run was misfiled under TRIAL-001, and the raw artifacts are now re-registered under TRIAL-002 artifact ids.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

- [x] `log:v2:module_trial:TRIAL-002:attempt-002` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-002:best` exists in Warehouse.
- [x] `checkpoint:v2:module_trial:TRIAL-002:attempt-002:full` exists in Warehouse.
- [x] `receipt:v2:module_trial:TRIAL-002:attempt-002:runner_console` exists in Warehouse.
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
