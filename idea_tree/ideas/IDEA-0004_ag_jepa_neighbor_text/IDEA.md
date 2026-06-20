# IDEA-0004：AG-JEPA 邻居文本变体

```text
idea_id: IDEA-0004
status: candidate
source_type: observation
source_status: unknown
global_score: 40
current_version_score:
  v1: 40
idea_dir: idea_tree/ideas/IDEA-0004_ag_jepa_neighbor_text/
```

## 来源

来源不明确。由未启用的 `use_ag_jepa_v2` 开关迁移而来。

## 基于什么

- `v1`
- AG-JEPA auxiliary training
- GPT text prototypes

## 假设

加入相邻类别文本作为 neighbor constraint，可能让 AG-JEPA patch prediction
不那么类别孤立，并提升语义平滑性。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 40 | direct | v1 已经使用 AG-JEPA，因此这是局部扩展。 |

## 阻塞点

- 判断这是本地想法还是论文支持。
- 检查是否会模糊细粒度类别边界。
