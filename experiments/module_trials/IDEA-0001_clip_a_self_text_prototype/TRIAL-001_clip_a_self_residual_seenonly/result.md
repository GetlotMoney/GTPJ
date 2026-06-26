# TRIAL-001_clip_a_self_residual_seenonly Result

## Metrics

| Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB | 5 | 72.32 | 75.19 | 73.72 | 81.13 | 30 |

## Baseline Comparison

| Baseline | H | Trial H | Delta H |
|---|---:|---:|---:|
| GTPJ-v1 authoritative baseline | 73.93 | 73.72 | -0.21 |
| CONFIRM-001 same-day confirmation | 73.77 | 73.72 | -0.05 |

## Evidence

```text
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-001
best_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-001:best
full_checkpoint_artifact_id: checkpoint:v1:module_trial:TRIAL-001:attempt-001:full
runner_console_artifact_id: receipt:v1:module_trial:TRIAL-001:attempt-001:runner_console
```

## Decision

`revise`。

CLIP-A-self residual seen-only did not beat the current v1 baseline. Keep the evidence, do not promote. If continuing this idea, next work should inspect prototype drift and then run a smaller outer-ratio or anchoring ablation rather than promote this trial.
