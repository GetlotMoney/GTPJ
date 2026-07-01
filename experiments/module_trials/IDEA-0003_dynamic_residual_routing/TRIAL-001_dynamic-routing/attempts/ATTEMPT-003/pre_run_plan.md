# ATTEMPT-003 Pre-Run Plan

## Scope

- Trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
- Server run: RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu
- Workflow profile: best-repro-tune-followup
- Batch size: 64
- Epochs: 30
- Seed: 5
- GPUs: 0,1

## Rationale

ATTEMPT-001 showed that the strongest dynamic signals were close to the static v5 control but
not strong enough for promotion. ATTEMPT-002 showed that batch_size=128 caused a broad control
collapse and is rejected. ATTEMPT-003 therefore returns to bs=64 and spends the budget on
reproducing the current best evidence plus narrow parameter tuning.

The first launch id, RUN-20260701-0009-dynroute-bs64-repro-tune50-2gpu, was stopped before
completion evidence because one controller hit a concurrent batch_status.json read/write race.
The formal run id is RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu after fixing runner
status writes to atomic replace plus short read retries.

## Job Budget

- 10 must_reproduce jobs:
  - static_v5_control x3
  - DR-008 local_class_h24_a0.001 x3
  - DR-023 direction_sample_h48_a0.003 x3
  - dynamic_fixed_all x1
- 20 direction_repro_tune jobs:
  - hidden width near 32-64
  - `weight_s2v` near 0.42-0.52
  - anchor near 0.001-0.007
- 8 local_repro_tune jobs:
  - local class/sample modes around hidden 16-48
  - lower local residual weights 0.10-0.20
- 6 pse_repro_tune jobs:
  - `dynamic_pse_mode` only `fixed` or `class`
  - outer ratio 0.55-0.65
- 6 combination_repro_tune jobs:
  - direction + local
  - direction + PSE
  - local + direction + PSE

## Guardrails

- Keep dynamic ICSA frozen.
- Keep batch_size=64.
- Do not use `dynamic_pse_mode=sample`.
- Use atomic runner status writes and short JSON read retries for two-controller safety.
- Retain only the best three saved model files per job artifact.
- Use workflow runner status and warehouse artifacts as the evidence source.

## Evaluation

Analyze with `analyze-dynamic-routing-batch` after completion.
Decision should prioritize:

- best single dynamic result
- reproduce cluster mean and variance
- U/S stability, not H alone
- failures and invalid configs
- comparison against H=74.45 reference boundary
