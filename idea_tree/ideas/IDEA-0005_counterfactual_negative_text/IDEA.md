# IDEA-0005：反事实负文本 margin

```text
idea_id: IDEA-0005
status: candidate
source_type: observation
source_status: unknown
global_score: 40
current_version_score:
  v1: 40
idea_dir: idea_tree/ideas/IDEA-0005_counterfactual_negative_text/
```

## 来源

来源不明确。由未启用的 `use_cf_neg_text` 开关迁移而来。

## 基于什么

- `v1`
- GPT text prototypes
- base logits

## 假设

挖掘 text-neighbor negative classes 并施加 margin，可能减少语义相近 seen classes 之间的混淆。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 40 | direct | 可以作为辅助 margin 测试，不改变 logits shape。 |

## 阻塞点

- 记录来源或 local-heuristic 理由。
- 防止 seen classes 被过度分离。
