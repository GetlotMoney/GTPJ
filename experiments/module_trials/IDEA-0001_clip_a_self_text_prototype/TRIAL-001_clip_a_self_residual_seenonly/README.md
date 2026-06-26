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
changed_files:
  - train_GTPJ_CUB.py
  - model/MyModel.py
  - experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/ATTEMPTS.md
  - experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/attempts/
attempts_table: ATTEMPTS.md
best_attempt_id: ATTEMPT-003
best_attempt_dir: attempts/ATTEMPT-003
confirmation_attempt_id: ATTEMPT-007
confirmation_attempt_dir: attempts/ATTEMPT-007
run_config: attempts/ATTEMPT-003/config.yaml
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-003
log_uri: warehouse://gtpj/runs/v1/module_trial/TRIAL-001/attempt-003/logs/training_log_CUB_2026-06-26_18-59-40.txt
log_sha256: 0bd779315d16adcdf0f78bede52a13caa1d3cf494b17940f5bb033e9bb50ab74
log_size_bytes: 92210
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
trial_decision: revise
promotion_decision: blocked
promote_to:
```

## Changed Files

| File | Change | Code layer |
|---|---|---|
| `train_GTPJ_CUB.py` | Adds sentence-level GPT/VDT encoding and routes `use_clip_a_self` runs through sentence-level caches. | yes |
| `model/MyModel.py` | Adds `CLIPASelfAdapter` and the seen/unseen text adaptation path behind `use_clip_a_self`. | yes |
| `experiments/module_trials/.../ATTEMPTS.md` | Records the parameter sweep from ATTEMPT-002 to ATTEMPT-006. | no |
| `experiments/module_trials/.../attempts/ATTEMPT-002..006/config.yaml` | Stores attempt-local hyperparameter changes. | no |

## Result

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| ATTEMPT-003 | CUB | 5 | 71.76 | 76.97 | 74.27 | 81.72 | 33 | `log:v1:module_trial:TRIAL-001:attempt-003` |
| ATTEMPT-007 | CUB | 5 | 70.82 | 76.80 | 73.69 | 80.91 | 33 | `log:v1:module_trial:TRIAL-001:attempt-007` |

## Attempts

See `ATTEMPTS.md` for the full sweep. Ranking by H:

1. `ATTEMPT-003`: H=74.27
2. `ATTEMPT-002`: H=73.99
3. `ATTEMPT-006`: H=73.96
4. `ATTEMPT-001`: H=73.72
5. `ATTEMPT-007`: H=73.69
6. `ATTEMPT-004`: H=73.58
7. `ATTEMPT-005`: H=72.69

## Promotion Gate

- [x] baseline H, best-attempt H, and delta H recorded.
- [x] class order, split, logits shape, and metric calculation unchanged.
- [x] switch-off path remains the validated TRIAL-001 implementation path.
- [x] best-attempt evidence directory and external artifact pointers are complete.
- [x] clean confirmation of the ATTEMPT-003 setting has been run as ATTEMPT-007.
- [ ] clean confirmation did not reproduce ATTEMPT-003; ATTEMPT-007 reached H=73.69, which is -0.58 below ATTEMPT-003 and -0.24 below v1.
- [ ] automatic promotion is allowed only after `trial_decision: promote` and `promotion_decision: promote`.

## Decision

`revise`

The current highest observed setting is `ATTEMPT-003` with `H=74.27`, but the clean confirmation run `ATTEMPT-007` reached only `H=73.69`. This fails to confirm the ATTEMPT-003 high point and is below the authoritative `v1` baseline `H=73.93`. TRIAL-001 should remain `revise`; do not promote it without a new stabilization hypothesis and another clean confirmation.
