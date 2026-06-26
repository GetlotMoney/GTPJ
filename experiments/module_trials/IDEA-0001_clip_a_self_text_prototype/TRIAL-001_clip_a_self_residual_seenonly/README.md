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
code_commit:
trial_decision: pending
promotion_decision: not_applicable
promote_to:
changed_files:
  - train_GTPJ_CUB.py
  - model/MyModel.py
  - experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/config.yaml
run_config: config.yaml
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
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

## Promotion Gate

- [ ] baseline H、trial H、delta H 已记录。
- [ ] U/S/ZS 没有不可接受退化。
- [ ] class order、split、logits shape、metric calculation 未改变。
- [ ] switch off 能回到 `v1` 行为。
- [ ] 证据目录、外部 artifact 指针和 code.diff 完整。
- [ ] `promotion_decision` 为 `promote` 后才允许进入自动 promotion gate。

## 决策

待运行。
