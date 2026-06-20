# IDEA-0003：Cosine-only CrossModal 打分与 anchor loss

```text
idea_id: IDEA-0003
status: candidate
source_type: observation
source_status: unknown
global_score: 35
current_version_score:
  v1: 35
idea_dir: idea_tree/ideas/IDEA-0003_cosine_only_scoring/
```

## 来源

来源不明确。由未启用的 `cosine_only` 路径迁移而来。

## 基于什么

- `v1`
- CrossModalTransformer
- Text Adapter
- base logits

## 假设

如果 anchor loss 能阻止 CLIP-space drift，直接使用 CrossModal cosine scoring
可能优于 additive correction。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 35 | needs_adaptation | 高风险，因为它会改变主打分路径。 |

## 阻塞点

- 严格 review 来源/理由。
- 检查 shape 和 unseen-geometry。
