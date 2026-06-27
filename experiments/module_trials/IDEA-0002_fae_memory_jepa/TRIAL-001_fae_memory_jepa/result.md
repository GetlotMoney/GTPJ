# TRIAL-001_fae_memory_jepa Result

## Summary

ATTEMPT-001 completed as a clean module-trial run from pre-run freeze commit `5ca8245e37856e426407612b1a95bcdcfbd92697`.

The attempt did not beat the active v2 baseline observation. Best H was `73.82`, versus v2 best_observed_H `74.29`, so the trial decision is `revise` and no promotion gate is triggered.

## Metrics

| Attempt ID | Seed | U | S | H | ZS | Best epoch | Delta H vs v2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ATTEMPT-001 | 5 | 70.32 | 77.68 | 73.82 | 81.39 | 34 | -0.47 |

## Evidence

```text
run_id: RUN-20260627-234226-trial001-fae-memory-jepa
pre_run_freeze_commit: 5ca8245e37856e426407612b1a95bcdcfbd92697
train_log_artifact_id: log:v2:module_trial:TRIAL-001:attempt-001
best_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-001:best
full_checkpoint_artifact_id: checkpoint:v2:module_trial:TRIAL-001:attempt-001:full
runner_console_artifact_id: receipt:v2:module_trial:TRIAL-001:attempt-001:runner_console
attempt_manifest: attempts/ATTEMPT-001/manifest.yaml
```

## Decision

`revise`.

Do not promote. The result is useful evidence that the current FAE-memory JEPA parameterization is weaker than active v2 on H. It does not prove the idea is impossible; the next valid step would be a narrow trial-internal param/ablation attempt only if the owner wants to keep exploring it.
