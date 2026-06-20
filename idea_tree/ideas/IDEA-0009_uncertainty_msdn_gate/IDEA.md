# IDEA-0009：不确定性感知 MSDN gate

```text
idea_id: IDEA-0009
status: candidate
source_type: observation
source_status: unknown
global_score: 50
current_version_score:
  v1: 50
idea_dir: idea_tree/ideas/IDEA-0009_uncertainty_msdn_gate/
```

## 来源

来源不明确。由未启用的 `use_uncertainty_msdn_gate` 开关迁移而来。

## 基于什么

- `v1`
- MSDN mutual branch distillation
- score_s2v
- score_v2s

## 假设

当分支不确定或意见不一致时，降低 mutual distillation 权重，可能避免错误共识被强化。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 50 | direct | v1 主动使用 MSDN，且 logits shape 不变。 |

## 阻塞点

- 记录 confidence-gating 来源或本地理由。
- 检查 gating 是否削弱当前有效的 distillation。
