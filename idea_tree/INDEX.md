# 总创意清单

当前正式版本视图：`idea_tree/versions/v4.md`

这是给人读的全局创意总表，只回答“有哪些创意”。
具体某个版本下一步试什么，请读取 `idea_tree/versions/vX.md`。

| Idea | 标题 | Idea 文件 | 来源状态 | 全局分 | 覆盖版本 | 全局状态 | 下一步 |
|---|---|---|---|---:|---|---|---|
| `IDEA-0001` | CLIP-A-self text prototype adapter | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | verified | 82.0 | `v1`, `v2`, `v3`, `v4` | validated | Use GTPJ-v4 as the current confirmed formal version; future work can inspect PSE/BVSA weight sensitivity or U/S balance from this baseline. |
| `IDEA-0002` | FAE-memory JEPA auxiliary loss | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | local_heuristic | 72.0 | `v2`, `v3`, `v4` | validated | Use GTPJ-v4 as the current confirmed formal version; future work should treat IDEA-0002 as inherited and focus on new mechanisms or controlled ablations. |

## 使用规则

- 本文件是总清单，不直接作为实验优先级队列。
- 按版本选择创新 trial 时，读取 `idea_tree/versions/<base_version>.md`。
- `idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。
