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
trial_decision: revise
promotion_decision: rejected
promote_to:
changed_files:
  - train_GTPJ_CUB.py
  - model/MyModel.py
  - experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/config.yaml
run_config: config.yaml
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-001
log_uri: warehouse://gtpj/runs/v1/module_trial/TRIAL-001/attempt-001/logs/training_log_CUB_2026-06-26_16-42-37.txt
log_sha256: 2749bb5c45909a996529dccee4a097f75b51153a7bcf861634ce14358df65a31
log_size_bytes: 91468
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
```

## 改动文件

| 文件 | 改动 | 是否属于代码层 |
|---|---|---|
| `train_GTPJ_CUB.py` | Adds sentence-level GPT/VDT encoding and passes seen/unseen sentence embeddings to `GTPJ` only when `use_clip_a_self=true`. | yes |
| `model/MyModel.py` | Adds `CLIPASelfAdapter` and routes seen text prototypes through it when the trial switch is enabled. | yes |
| `config/versions/v1.yaml` | Unchanged. | no |
| `experiments/v1/config.yaml` | Unchanged. | no |
| `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/config.yaml` | Trial-local switch/config. | no |

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB | 5 | 72.32 | 75.19 | 73.72 | 81.13 | 30 | `log:v1:module_trial:TRIAL-001:attempt-001` |

## Promotion Gate

- [x] baseline H、trial H、delta H 已记录。
- [x] U/S/ZS 没有不可接受退化。
- [x] class order、split、logits shape、metric calculation 未改变。
- [x] switch off 能回到 `v1` 行为。
- [x] 证据目录、外部 artifact 指针和 code.diff 完整。
- [ ] `promotion_decision` 为 `promote` 后才允许进入自动 promotion gate。

## 决策

`revise`。

TRIAL-001 的 H=73.72，低于权威 v1 baseline H=73.93，也略低于当天 confirmation H=73.77。结果说明 CLIP-A-self residual seen-only 版本没有超过当前 v1；保留证据，不进入 promotion。后续若继续，应先分析 prototype drift 或尝试更小 outer ratio / L2SP anchoring ablation。
