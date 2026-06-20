# IDEA-0006：几何感知属性路由

```text
idea_id: IDEA-0006
status: candidate
source_type: observation
source_status: unknown
global_score: 50
current_version_score:
  v1: 50
idea_dir: idea_tree/ideas/IDEA-0006_geo_attribute_routing/
```

## 来源

来源不明确。由未启用的 `use_geo_attr_routing` 开关迁移而来。

## 基于什么

- `v1`
- FAE geometry-aware local encoding
- CUB expert attributes
- CLIP attribute text

## 假设

把局部视觉特征路由到类别相关的属性文本，可能提升可解释的 part-attribute grounding。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 50 | direct | v1 已经传递 class attributes 和 CLIP attribute text。 |

## 阻塞点

- 找来源支持，或标记为 local heuristic。
- 验证 attribute tensor 是否可用。
