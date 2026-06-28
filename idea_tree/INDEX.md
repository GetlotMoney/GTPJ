# 总创意清单

当前实验版本视图：`idea_tree/versions/v2.md`

这是给人读的全局创意总表，只回答“有哪些创意”。
具体某个版本下一步试什么，请读取 `idea_tree/versions/vX.md`。

| Idea | 标题 | Idea 文件 | 来源状态 | 全局分 | 覆盖版本 | 全局状态 | 下一步 |
|---|---|---|---|---:|---|---|---|
| `IDEA-0001` | CLIP-A-self text prototype adapter | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | verified | 82.0 | `v1`, `v2` | validated | Run GTPJ-v2 confirmation and U/S gap analysis before manuscript-grade claims; then continue v2 tune or ablation from config/versions/v2.yaml. |
| `IDEA-0002` | FAE-memory JEPA auxiliary loss | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | local_heuristic | 72.0 | `v2` | weakened | TRIAL-002 ATTEMPT-009 synchronized as not_confirmed: H=74.14, delta_H=-0.15 vs v2 best_observed_H=74.29 (unconfirmed); do not promote/tag before v2 clean confirmation. |

## 使用规则

- 本文件是总清单，不直接作为实验优先级队列。
- 按版本选择创新 trial 时，读取 `idea_tree/versions/<base_version>.md`。
- `idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。
