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
  - experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/config.yaml
attempts_table: ATTEMPTS.md
best_attempt_id: ATTEMPT-001
best_attempt_dir: .
run_config: config.yaml
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-001
log_uri: warehouse://gtpj/runs/v1/module_trial/TRIAL-001/attempt-001/logs/training_log_CUB_2026-06-26_16-42-37.txt
log_sha256: 2749bb5c45909a996529dccee4a097f75b51153a7bcf861634ce14358df65a31
log_size_bytes: 91468
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
trial_decision: revise
promotion_decision: rejected
promote_to:
```

## Changed Files

| File | Change | Code layer |
|---|---|---|
| `train_GTPJ_CUB.py` | Adds sentence-level GPT/VDT encoding and passes seen/unseen sentence embeddings to `GTPJ` only when `use_clip_a_self=true`. | yes |
| `model/MyModel.py` | Adds `CLIPASelfAdapter` and routes seen text prototypes through it when the trial switch is enabled. | yes |
| `config/versions/v1.yaml` | Unchanged. | no |
| `experiments/v1/config.yaml` | Unchanged. | no |
| `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/config.yaml` | Trial-local switch/config. | no |

## Result

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| ATTEMPT-001 | CUB | 5 | 72.32 | 75.19 | 73.72 | 81.13 | 30 | `log:v1:module_trial:TRIAL-001:attempt-001` |

## Attempts

TRIAL-001 currently has one recorded attempt. See `ATTEMPTS.md` for the attempt index.

## Promotion Gate

- [x] baseline H, trial H, and delta H recorded.
- [x] U/S/ZS have no unacceptable regression.
- [x] class order, split, logits shape, and metric calculation unchanged.
- [x] switch-off path returns to `v1` behavior.
- [x] evidence directory, external artifact pointers, and `code.diff` are complete.
- [ ] automatic promotion is allowed only after `promotion_decision: promote`.

## Decision

`revise`

TRIAL-001 reached `H=73.72`, below the authoritative `v1` baseline `H=73.93`, and slightly below the same-day confirmation `H=73.77`. The evidence should be kept, but this trial should not enter promotion. If this idea continues, the next step should focus on prototype drift and then test a smaller outer ratio or an anchoring follow-up.
