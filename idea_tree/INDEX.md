# 总创意清单

当前实验版本视图：`idea_tree/versions/v5.md`

这是给人读的全局创意总表，只回答“有哪些创意、主要机制是什么”。
它是各版本挑选 idea 的公共菜市场，不记录任何局部执行动作或实验计划。

| Idea | 标题 | 主要内容 | Idea 文件 | 来源状态 | 全局分 | 覆盖版本 | 全局状态 |
|---|---|---|---|---:|---|---|---|
| `IDEA-0001` | CLIP-A-self text prototype adapter | 用 CLIP-A-self 对 seen-class GPT/VDT 句子描述做自注意力聚合，增强文本原型适配器，同时保持 GZSL 接口不变。 | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | verified | 82.0 | `v1`, `v2`, `v3`, `v4`, `v5` | validated |
| `IDEA-0003` | Dynamic Residual Routing | 把 v5 中固定 residual/mix 系数改成可学习 dynamic gates，按样本或类别调节 local、ICSA、BVSA direction 和 PSE routing。 | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | local_heuristic | 78.0 | `v5` | weakened |
| `IDEA-0013` | 干净 V6 框架候选 | 把 8 句话作为 6 个局部部位、1 个独特判别特征、1 个全局描述，删除 V5 旧频域/拓扑/多辅助损失干扰，用干净的句子—区域匹配框架先证明核心机制是否合理。 | `idea_tree/ideas/IDEA-0013_clean_v6_candidate/IDEA.md` | local_heuristic | 78.0 | `v5` | testing |
| `IDEA-0002` | FAE-memory JEPA auxiliary loss | 把 JEPA 辅助损失的视觉 context 移到 FAE memory，用 FAE-enhanced context 预测 detached pre-FAE patch target。 | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | local_heuristic | 72.0 | `v2`, `v3`, `v4`, `v5` | validated |
| `IDEA-0011` | 图像条件 PSE 选句 | 保留 PSE 和原局部分支，只让全局图像对 8 句话生成句子权重，检验“全局选句”是否足够。 | `idea_tree/ideas/IDEA-0011_image_conditioned_pse/IDEA.md` | local_heuristic | 62.0 | `v5` | rejected |
| `IDEA-0012` | PSE + VSCE 双向句子区域匹配 | 用同一张 8 句 × 图像全局/Top-K 区域匹配表，同时生成句子权重和局部区域权重，检验统一句子—区域匹配是否优于实验 A。 | `idea_tree/ideas/IDEA-0012_pse_vsce/IDEA.md` | local_heuristic | 61.0 | `v5` | rejected |

## 使用规则

- 本文件是总清单，不直接作为实验优先级队列。
- 按版本选择创新 trial 时，读取 `idea_tree/versions/<base_version>.md`。
- 具体执行动作只能写入版本队列、trial/attempt 记录、task card 或实验结果文件，不写入本总表。
- `idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。
