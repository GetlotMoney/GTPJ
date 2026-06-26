# ATTEMPT-008 Result

## Metrics

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT-008 | CUB | 5 | 71.36 | 76.58 | 73.88 | 81.22 | 33 |

## Comparison

| Reference | H | Delta vs ATTEMPT-008 |
|---|---:|---:|
| ATTEMPT-003 target | 74.27 | -0.39 |
| ATTEMPT-007 clean confirmation | 73.69 | +0.19 |
| GTPJ-v1 authoritative baseline | 73.93 | -0.05 |

## Evidence

```text
run_id: RUN-20260626-231504-module-trial-attempt-008
pre_run_freeze_commit: 8b6acac45b83cca1a255d00782d4eba7a272c4fb
config_sha256: 2970fa444cdee33f5690198018f39bd10c801d53c74d03eec8886ecc8fe63622
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-008
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-008:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-008:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-008:runner_console
```

## Decision

`not_confirmed`

ATTEMPT-008 was a second clean rerun of the ATTEMPT-003 config. It reached `H=73.88`, which is closer to the v1 baseline than ATTEMPT-007 but still does not reproduce ATTEMPT-003. Keep TRIAL-001 in revise and do not promote from ATTEMPT-003.
