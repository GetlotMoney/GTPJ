# TRIAL-001_fae_memory_jepa

```text
trial_id: TRIAL-001
idea_id: IDEA-0002
base_version: v2
base_code_tag: v2
branch_source: main
idea_source_file: idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md
idea_title: FAE-memory JEPA auxiliary loss
version_score: 72.0
applicability: needs_adaptation
code_branch: dev/v2-idea-0002-trial-001-fae-memory-jepa
code_tag: trial/v2/idea-0002/trial-001
code_commit: pending_pre_run_freeze_commit
trial_decision: pending
promotion_decision: not_applicable
promote_to:
evidence_level: pending
best_observed_H:
confirmed_H:
confirmation_status: pending
changed_files:
run_config: attempts/ATTEMPT-001/config.yaml
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
idea_intent_check: idea_intent_check.md
interface_precheck: interface_precheck.md
review_round_1: review_round_1.md
interface_check: interface_check.md
review_round_2: review_round_2.md
agent_summary: agent_summary.md
```

## 改动文件

| 文件 | 改动 | 是否属于代码层 |
|---|---|---|
| `model/MyModel.py` | Add `jepa_context_mode` and FAE-memory JEPA auxiliary path | yes |
| `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-001_fae_memory_jepa/attempts/ATTEMPT-001/config.yaml` | Enable `jepa_context_mode: fae_memory` | no |
| `tests/test_fae_memory_jepa.py` | Gradient and shape smoke tests | no |
| `train_GTPJ_CUB.py` | Log `jepa_context_mode` in training header | yes |

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## Innovation Code Review

```text
Review 0: idea_intent_check.md
Review 1: interface_precheck.md
Review 2: review_round_1.md + interface_check.md + quality_check.md
Review 3: review_round_2.md + agent_summary.md
activation_mode: real_multi_agent
```

## Promotion Gate

- [ ] baseline H、trial H、delta H 已记录。
- [ ] `evidence_level: baseline_grade`；单次最高 H 只能写 `best_observed_H`。
- [ ] clean confirmation 或多 run 稳定性证据明确，`confirmed_H` 和 `confirmation_status` 已记录。
- [ ] U/S/ZS 没有不可接受退化。
- [ ] class order、split、logits shape、metric calculation 未改变。
- [ ] switch off 能回到 `v2` 行为。
- [ ] 证据目录、外部 artifact 指针和 code.diff 完整。
- [ ] `promotion_decision` 为 `promote` 后才允许进入自动 promotion gate。

## 决策

待记录。
