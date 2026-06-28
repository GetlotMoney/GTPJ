# 2026-06-28 TRIAL-002 Reproducibility Diagnostics

## ISSUE-20260628-014: Same-seed confirmation produced mixed results

### Symptom

`TRIAL-002_strict_conditional_jepa` used the same frozen config and seed for confirmation reruns, but the result crossed the decision boundary inconsistently:

- `ATTEMPT-002`: H=74.24, best_epoch=33
- `ATTEMPT-003`: H=73.81, best_epoch=42, not confirmed
- `ATTEMPT-004`: H=74.27, best_epoch=33

### Impact

The result can stay as `best_observed_H`, but it cannot be promoted to `confirmed_H`, `baseline_grade`, a formal tag, or a 10-run tune sweep starting point until reproducibility is diagnosed.

### Root Cause

The old training logs recorded `random_seed`, but did not record the runtime determinism state or isolate batch sampling. That made it impossible to quickly tell whether the mixed result came from:

- config/run artifact mismatch;
- batch sampling RNG drift;
- CUDA/cuDNN/PyTorch nondeterministic kernels;
- normal optimizer sensitivity around a narrow metric boundary.

### Fix

- Add explicit training-log fields for `strict_determinism`, `use_dedicated_batch_rng`, `batch_sampling_seed`, torch/cuda version, cuDNN benchmark/deterministic flags, deterministic algorithms, and CUBLAS workspace config.
- Add optional `strict_determinism`, `deterministic_warn_only`, `use_dedicated_batch_rng`, and `batch_sampling_seed` config controls.
- Route training batch `randperm` / `randint` through the optional dedicated CPU generator when enabled.
- Add tests proving the dedicated batch generator replays the same sequence and is independent from unrelated global RNG calls.
- Update `sync-trial-summary` so `not_confirmed` diagnostic closeout can point root review/agent summaries at the latest attempt without overwriting the existing trial `best_observed_H`.

### Prevention Rule

When same-config, same-seed confirmation is mixed, mark `mixed_confirmation` and run reproducibility diagnosis before tune, promotion, or tag. Do not ask the owner to remember that a result might be fake or unconfirmed.

### Helper Follow-up

Future helper enhancement: `closeout-check` or a dedicated `repro-diagnose` command should compare same-config attempts and warn when the H spread crosses a configured tolerance while `confirmed_H` is still pending.
