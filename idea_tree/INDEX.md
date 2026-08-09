# 总创意清单

当前实验版本视图：`idea_tree/versions/v5.md`

这是给人读的全局创意总表，只回答“有哪些创意、主要机制是什么”。
它是各版本挑选 idea 的公共菜市场，不记录任何局部执行动作或实验计划。

| Idea | 标题 | 主要内容 | Idea 文件 | 来源状态 | 全局分 | 覆盖版本 | 全局状态 |
|---|---|---|---|---:|---|---|---|
| `IDEA-0001` | CLIP-A-self text prototype adapter | 用 CLIP-A-self 对 seen-class GPT/VDT 句子描述做自注意力聚合，增强文本原型适配器，同时保持 GZSL 接口不变。 | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | verified | 82.0 | `v1`, `v2`, `v3`, `v4`, `v5` | validated |
| `IDEA-0012` | PSE 与 VSCE 双向交互 | 让 PSE 保留的 8 个增强句子与全局图像、Top-K 32 局部区域建立统一匹配表，再用双向 logsumexp 同时生成句子权重和区域权重。 | `idea_tree/ideas/IDEA-0012_pse_vsce_bidirectional_interaction/IDEA.md` | local_heuristic | 82.0 | `v5` | selected |
| `IDEA-0003` | Dynamic Residual Routing | 把 v5 中固定 residual/mix 系数改成可学习 dynamic gates，按样本或类别调节 local、ICSA、BVSA direction 和 PSE routing。 | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | local_heuristic | 78.0 | `v5` | weakened |
| `IDEA-0002` | FAE-memory JEPA auxiliary loss | 把 JEPA 辅助损失的视觉 context 移到 FAE memory，用 FAE-enhanced context 预测 detached pre-FAE patch target。 | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | local_heuristic | 72.0 | `v2`, `v3`, `v4`, `v5` | validated |

## 使用规则

- 本文件是总清单，不直接作为实验优先级队列。
- 按版本选择创新 trial 时，读取 `idea_tree/versions/<base_version>.md`。
- 具体执行动作只能写入版本队列、trial/attempt 记录、task card 或实验结果文件，不写入本总表。
- `idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。
