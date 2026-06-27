# GTPJ-v2 Baseline

```text
version: v2
code_tag: v2
baseline_name: GTPJ-v2
parent_version: v1
parent_tag: v1
dataset: CUB GZSL
seed: 5
source_trial: experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly
source_attempt: ATTEMPT-019
source_trial_run_commit: 453acc0
config: config.yaml
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-019
log_uri: warehouse://gtpj/runs/v1/module_trial/TRIAL-001/attempt-019/logs/training_log_CUB_2026-06-27_01-27-48.txt
log_sha256: 8d49983c455ca5ce1d52336d8294a4a1eaa8acc6f43b46bc5cef100f015fd59c
log_size_bytes: 92057
status: owner_activated_unconfirmed
evidence_level: valid_single_run
best_observed_H: 74.29
confirmed_H: pending
confirmation_status: needs_confirmation
```

## Purpose

This directory records the owner-activated `GTPJ-v2` mainline evidence. It is based on the
current best CLIP-A-self module trial result, not on a separate version-level confirmation run;
therefore `H=74.29` is `best_observed_H`, not `confirmed_H`.

## Key Configuration

| Parameter | Value |
|---|---:|
| `use_clip_a_self` | true |
| `clip_a_self_apply_unseen` | false |
| `clip_a_self_heads` | 4 |
| `clip_a_self_dropout` | 0.5 |
| `clip_a_self_inner_ratio` | 0.35 |
| `clip_a_self_outer_ratio` | 0.15 |
| `conditional_text_ratio` | 0.008 |

Training schedule:

```text
stage 1: lr=0.001, epochs=20, eta_min=1e-5
stage 2: lr=0.0001, epochs=20, eta_min=1e-6, restart_from_best=False
stage 3: lr=0.00001, epochs=10, eta_min=1e-7, restart_from_best=False
total_epochs: 50
```

## Result

| Dataset | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | 33 | `warehouse://gtpj/runs/v1/module_trial/TRIAL-001/attempt-019/logs/training_log_CUB_2026-06-27_01-27-48.txt` |

## Known Risks

- `ATTEMPT-019` has not yet received an independent clean confirmation rerun.
- The result is seen-heavy: `S - U = 6.20`.
- Future manuscript-grade evidence should add v2 confirmation and ablation runs.

## Conclusion

The accepted CUB seed=5 owner-activated mainline result for `GTPJ-v2` is
`best_observed_H=74.29`. Future module trials, tuning, ablations, and confirmation runs
should treat `v2` as the active code/config baseline unless the owner explicitly switches
back to another version. Do not describe `74.29` as `confirmed_H` until clean confirmation passes.
