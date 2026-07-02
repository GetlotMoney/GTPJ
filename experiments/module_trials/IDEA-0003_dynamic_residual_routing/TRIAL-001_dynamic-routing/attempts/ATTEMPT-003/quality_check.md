# ATTEMPT-003 Quality Check

```text
attempt_id: ATTEMPT-003
trial_id: TRIAL-001
subject_id: ATTEMPT-003
subject_type: attempt
evidence_state: tune_promising
transition_id: ER-20260702-ATTEMPT003-004
quality_decision: allow_as_tune_promising
promotion_decision: blocked
evidence_level: valid_single_batch
confirmation_status: needs_confirmation
```

## Evidence Boundary

- Runtime evidence stays on `lab4090` under `.gtpj_runtime/batches/`.
- GitHub records summary metrics, hashes, sizes, decisions, and artifact URIs.
- No raw logs, checkpoints, generated figures, or cache files were added to GitHub.

## Epoch Schedule Check

```text
config_epochs_field: 30
planned_train_epochs: 50
epoch_schedule_source: lr_stages
lr_stages: 20 + 20 + 10
```

The true training length is 50 epochs because `lr_stages` overrides the legacy
`epochs` field.

## Checks

- [x] Code snapshot and base version are explicit.
- [x] Config copy is saved in the attempt directory.
- [x] Runtime summary, status, plan, events, hashes, sizes, and locations are recorded.
- [x] Result semantics are GZSL U/S/H/ZS from the protected evaluator.
- [x] `evidence_level`, `best_observed_H`, `confirmed_H`, and `confirmation_status` are separated.
- [x] No eval, class order, logits shape, split, or label mapping change is declared or observed.
- [x] GZSL hard rules are represented in `TRANSITIONS.jsonl` rule checks.
- [x] `current_state` is derived from `TRANSITIONS.jsonl`.
- [x] GitHub does not contain raw logs, checkpoints, generated figures, or cache files.
- [x] Checkpoint retention was applied to the current run's copied model weights.

## Runtime Findings

- `RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` completed 50 / 50 jobs with 0 failures.
- The best single job was `DR-018 direction_sample_h48_w0.5_a0.003` at H=74.86.
- `DR-023 direction_sample_h48_a0.003` reproduced at mean H=74.60 over 3 runs.
- `DR-008 local_class_h24_a0.001` reproduced weaker at mean H=74.28 over 3 runs.
- Static v5 control reproduced at mean H=74.49 over 3 runs, so this batch does not show the bs=128 collapse.

## Checkpoint Retention

Retention was applied on 2026-07-02 to the current `RUN-20260701-0010` copied
`best_model_*.pth` files only.

```text
copied_model_files_seen: 49
deleted_model_checkpoint_files: 46
retained_model_checkpoint_files: 3
```

Retained current-run checkpoints:

| Job | H | SHA256 | Size bytes | Path |
|---|---:|---|---:|---|
| DR-018 | 74.86 | `2ed456b75483707873fdf765c120d47ccae52128e577d17594ffd3fa974b08e1` | 102790544 | `/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/attempt-018/logs/best_model_CUB_2026-07-01_15-20-51_H7486.pth` |
| DR-019 | 74.82 | `61686727a0b427898d5fd35ab2c9714fa0a385fbf47a5d65bc7f71e0279585b3` | 102790544 | `/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/attempt-019/logs/best_model_CUB_2026-07-01_15-28-47_H7482.pth` |
| DR-016 | 74.69 | `4141ef8393db4854fa55a25ef309bc6cc664ddad71a817d68d108c1da8e7fd4d` | 102790544 | `/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/attempt-016/logs/best_model_CUB_2026-07-01_15-10-48_H7469.pth` |

## Blocking Issues

None for recording `ATTEMPT-003` as `tune_promising`.

Promotion remains blocked because the new top single result needs min3
confirmation and direction-gate ablation.
