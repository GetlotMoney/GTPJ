# 2026-06-28 TRIAL-002 Reproducibility Diagnostics

## ISSUE-20260628-014: Same-seed confirmation produced mixed results

### Symptom

`TRIAL-002_strict_conditional_jepa` used the same frozen config and seed for confirmation reruns, but the result crossed the decision boundary inconsistently:

- `ATTEMPT-002`: H=74.24, best_epoch=33
- `ATTEMPT-003`: H=73.81, best_epoch=42, not confirmed
- `ATTEMPT-004`: H=74.27, best_epoch=33
- `ATTEMPT-005`: H=73.79, best_epoch=43, strict determinism + dedicated batch RNG
- `ATTEMPT-006`: H=73.91, best_epoch=42, exact deterministic rerun of ATTEMPT-005
- `ATTEMPT-007`: H=73.94, best_epoch=42, same deterministic diagnosis path with `random_seed=42` and `batch_sampling_seed=42`
- `ATTEMPT-008`: H=73.83, best_epoch=45, exact seed-42 deterministic rerun of ATTEMPT-007

### Impact

The result can stay as `best_observed_H`, but it cannot be promoted to `confirmed_H`, `baseline_grade`, a formal tag, or a 10-run tune sweep starting point until reproducibility is diagnosed.
After ATTEMPT-005/006 and ATTEMPT-007/008, the diagnosis result is that the strict path is still below the 74-level line under deterministic controls, so tuning and promotion remain blocked.

### Root Cause

The old training logs recorded `random_seed`, but did not record the runtime determinism state or isolate batch sampling. That made it impossible to quickly tell whether the mixed result came from:

- config/run artifact mismatch;
- batch sampling RNG drift;
- CUDA/cuDNN/PyTorch nondeterministic kernels;
- normal optimizer sensitivity around a narrow metric boundary.

ATTEMPT-007/008 runner console receipts preserve a PyTorch warning that memory-efficient attention defaults to a non-deterministic backward algorithm when deterministic algorithms are enabled with `warn_only=True`. That warning does not invalidate the completed runs, but it explains why exact replay is not guaranteed yet.

### Fix

- Add explicit training-log fields for `strict_determinism`, `use_dedicated_batch_rng`, `batch_sampling_seed`, torch/cuda version, cuDNN benchmark/deterministic flags, deterministic algorithms, and CUBLAS workspace config.
- Add optional `strict_determinism`, `deterministic_warn_only`, `use_dedicated_batch_rng`, and `batch_sampling_seed` config controls.
- Route training batch `randperm` / `randint` through the optional dedicated CPU generator when enabled.
- Add tests proving the dedicated batch generator replays the same sequence and is independent from unrelated global RNG calls.
- Update `sync-trial-summary` so `not_confirmed` diagnostic closeout can point root review/agent summaries at the latest attempt without overwriting the existing trial `best_observed_H`.
- For the next strict reproducibility check, either set `deterministic_warn_only=false` to fail fast on non-deterministic kernels or replace/disable the memory-efficient attention path for the diagnostic run.

### Prevention Rule

When same-config, same-seed confirmation is mixed, mark `mixed_confirmation` and run reproducibility diagnosis before tune, promotion, or tag. Do not ask the owner to remember that a result might be fake or unconfirmed.

### Helper Follow-up

Future helper enhancement: `closeout-check` or a dedicated `repro-diagnose` command should compare same-config attempts and warn when the H spread crosses a configured tolerance while `confirmed_H` is still pending.
