# IDEA-0008：属性-patch OT 对齐

```text
idea_id: IDEA-0008
status: candidate
source_type: hybrid
source_status: unverified
global_score: 50
current_version_score:
  v1: 50
idea_dir: idea_tree/ideas/IDEA-0008_attr_patch_ot/
```

## 来源

使用 optimal-transport 风格的 Sinkhorn matching，但 GTPJ 中该模块的精确来源尚未验证。

## 基于什么

- `v1`
- FAE geometry-aware local encoding
- CUB expert attributes
- CLIP attribute text

## 假设

局部 patch 与类别相关属性之间的 soft OT alignment，可能提升细粒度 part grounding。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 50 | direct | v1 有 FAE patches 和 attribute text 输入。 |

## 阻塞点

- 验证 OT/patch-attribute grounding 来源。
- 检查数值稳定性。
