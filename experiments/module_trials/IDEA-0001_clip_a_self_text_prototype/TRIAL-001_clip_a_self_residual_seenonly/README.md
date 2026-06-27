# TRIAL-001_clip_a_self_residual_seenonly

```text
trial_id: TRIAL-001
idea_id: IDEA-0001
base_version: v1
base_code_tag: v1
branch_source: main
idea_source_file: idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md
idea_title: CLIP-A-self text prototype adapter
version_score: 78.0
applicability: needs_adaptation
code_branch: dev/v1-idea-0001-trial-001-clip-a-self-residual-seenonly
code_tag: trial/v1/idea-0001/trial-001
code_commit: da2e295cb15b0d55afdcf4785bce4bc6a4bff80e
best_attempt_id: ATTEMPT-019
best_attempt_dir: attempts/ATTEMPT-019
best_attempt_run_commit: 453acc0
best_attempt_record_commit: 3a7945a
run_config: attempts/ATTEMPT-019/config.yaml
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-019
log_uri: warehouse://gtpj/runs/v1/module_trial/TRIAL-001/attempt-019/logs/training_log_CUB_2026-06-27_01-27-48.txt
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
trial_decision: promote
promotion_decision: blocked
promote_to: v2
evidence_level: valid_single_run
best_observed_H: 74.29
confirmed_H: pending
confirmation_status: needs_confirmation
```

## Changed Files

| File | Change | Code layer |
|---|---|---|
| `train_GTPJ_CUB.py` | Adds sentence-level GPT/VDT encoding and routes `use_clip_a_self` runs through sentence-level caches. | yes |
| `model/MyModel.py` | Adds `CLIPASelfAdapter` and the seen/unseen text adaptation path behind `use_clip_a_self`. | yes |
| `experiments/module_trials/.../ATTEMPTS.md` | Records the trial-internal parameter sweep and confirmation attempts. | no |
| `experiments/module_trials/.../attempts/` | Stores attempt-local configs, manifests, results, and quality checks. | no |

## Current Best Observed

| Attempt ID | Dataset | Seed | Heads | Dropout | Inner | Outer | U | S | H | ZS | Best epoch | Log artifact |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ATTEMPT-019 | CUB | 5 | 4 | 0.5 | 0.35 | 0.15 | 71.32 | 77.52 | 74.29 | 81.59 | 33 | `log:v1:module_trial:TRIAL-001:attempt-019` |

## Recent Sweep Summary

| Attempt ID | Inner | Outer | U | S | H | ZS | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| ATTEMPT-009 | 0.25 | 0.100 | 70.83 | 77.03 | 73.80 | 81.22 | not_confirmed |
| ATTEMPT-010 | 0.25 | 0.125 | 70.76 | 77.49 | 73.97 | 81.22 | keep |
| ATTEMPT-011 | 0.25 | 0.150 | 70.76 | 77.54 | 74.00 | 81.19 | keep |
| ATTEMPT-012 | 0.25 | 0.175 | 71.19 | 77.08 | 74.02 | 81.22 | keep |
| ATTEMPT-013 | 0.30 | 0.100 | 71.19 | 76.52 | 73.76 | 80.91 | reject |
| ATTEMPT-014 | 0.30 | 0.125 | 71.35 | 76.99 | 74.07 | 81.28 | keep |
| ATTEMPT-015 | 0.30 | 0.150 | 70.99 | 77.88 | 74.27 | 81.45 | keep |
| ATTEMPT-016 | 0.30 | 0.175 | 70.85 | 77.12 | 73.85 | 81.05 | reject |
| ATTEMPT-017 | 0.35 | 0.100 | 71.59 | 76.32 | 73.88 | 81.21 | reject |
| ATTEMPT-018 | 0.35 | 0.125 | 71.08 | 77.42 | 74.12 | 81.51 | keep |
| ATTEMPT-019 | 0.35 | 0.150 | 71.32 | 77.52 | 74.29 | 81.59 | best |
| ATTEMPT-020 | 0.35 | 0.175 | 71.13 | 77.63 | 74.24 | 81.42 | keep |

`ATTEMPT-021` failed before training epochs began and is recorded as a runner/environment issue in
`docs/workflow/issues/2026-06-27-trial001-batch-runner-and-tag-boundary.md`; it is not valid
result evidence. `ATTEMPT-021` through `ATTEMPT-028` remain uncompleted.

## Promotion Gate

- [x] baseline H, current best H, and delta H recorded.
- [x] class order, split, logits shape, and metric calculation unchanged.
- [x] switch-off path remains the validated TRIAL-001 implementation path.
- [x] current best attempt evidence directory and external artifact pointers are complete.
- [x] raw logs, checkpoints, and runner receipts are registered in Warehouse rather than Git.
- [x] owner accepted `ATTEMPT-019` as `GTPJ-v2` current mainline code evidence on 2026-06-27.
- [x] `ATTEMPT-019` is recorded as `best_observed_H=74.29`.
- [x] `promotion_decision: blocked` is recorded until clean confirmation passes.
- [ ] current best `ATTEMPT-019` has not yet received a clean confirmation rerun; this remains a follow-up requirement.
- [ ] U/S gap remains large: `S - U = 6.20`, so the result is seen-heavy.

## Decision

`owner_activated_unconfirmed`

`ATTEMPT-019` is now the best observed recorded experiment for TRIAL-001 with `H=74.29`
(`U=71.32`, `S=77.52`, `ZS=81.59`, best epoch 33). It is recorded through the
attempt ledger and external artifact ids, not through an attempt-level git tag. By owner decision on
2026-06-27, this trial is activated as the current `GTPJ-v2` mainline code while preserving
the clean-confirmation and seen-heavy follow-up risks. It is not baseline-grade until clean confirmation passes.
