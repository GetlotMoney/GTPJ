# IDEA-0016：双原型专家融合（DPEF）

```text
idea_id: IDEA-0016
title: 双原型专家融合（DPEF）
status: candidate
source_type: observation
source_ref: legacy_unmerged_rpr@1b8f599a/RUN-002 + 2026-08-16 debug score-search
source_status: local_heuristic
global_score: 82.0
idea_dir: idea_tree/ideas/IDEA-0016_dual_prototype_expert_fusion/
```

## 第一性原理

旧全局实验表明：强 seen-only 原型映射能提高联合分类，但不迁移 unseen；SharedPSE 能改善 unseen 文本原型，却削弱 seen/unseen 联合平衡。DPEF 不再继续堆注意力，而是把两类已验证能力保留为两个专家，在已知 GZSL 类别 split 上做归一化原型融合。

## 可解释输出

每个类别保留 `raw / strong / shared / fused` 四个原型及夹角；两个全局融合系数直接说明最终原型来自哪个专家，不把 attention 权重冒充解释。

## 边界

当前公式的 `(a,b)` 在 official test 上搜索，只能作为性能候选，不是 confirmation 或论文泛化证据。它也不宣称原型融合本身为首创；真正论文新颖性仍需 validation-selected 版本、消融与完整相关工作检索。
