# IDEA-0007：拓扑感知文本属性库

```text
idea_id: IDEA-0007
status: candidate
source_type: observation
source_status: unknown
global_score: 45
current_version_score:
  v1: 45
idea_dir: idea_tree/ideas/IDEA-0007_text_attribute_reservoir/
```

## 来源

来源不明确。由未启用的 `use_text_attr_reservoir` 开关迁移而来。

## 基于什么

- `v1`
- GPT text prototypes
- CUB expert attributes
- CLIP attribute text
- topology-preserving text constraint

## 假设

把 attribute-text reservoir 信息注入 class prototypes，可能丰富语义；
同时 topology loss 可以限制表示漂移。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 45 | needs_adaptation | 可能有用，但可能扭曲 GPT/CLIP text geometry。 |

## 阻塞点

- 澄清来源。
- 检查 text topology drift。
