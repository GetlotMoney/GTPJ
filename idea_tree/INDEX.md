# 创意树索引

当前框架版本：`v1`

这是给人读的主列表。当前工作窗口优先按
`v1` 分数排序。`global_score` 表示长期价值，
不直接决定当前实验顺序。

| 排名 | Idea | 标题 | Idea 文件 | 来源状态 | 全局分 | 当前分 | 适用性 | 状态 | 下一步 |
|---:|---|---|---|---|---:|---:|---|---|---|
| 1 | `IDEA-0001` | LaSt-ViT CLS 替换 | `idea_tree/ideas/IDEA-0001_lastvit_cls/IDEA.md` | unverified | 55 | 55 | needs_adaptation | candidate | 验证引用论文/来源，然后决定是否创建小型模块 trial。 |
| 2 | `IDEA-0008` | 属性-patch OT 对齐 | `idea_tree/ideas/IDEA-0008_attr_patch_ot/IDEA.md` | unverified | 50 | 50 | direct | candidate | trial 前验证 OT/patch-attribute 的来源依据。 |
| 3 | `IDEA-0006` | 几何感知属性路由 | `idea_tree/ideas/IDEA-0006_geo_attribute_routing/IDEA.md` | unknown | 50 | 50 | direct | candidate | 为 attribute routing 找论文/来源支持，或在 trial 前标记为本地想法。 |
| 4 | `IDEA-0009` | 不确定性感知 MSDN gate | `idea_tree/ideas/IDEA-0009_uncertainty_msdn_gate/IDEA.md` | unknown | 50 | 50 | direct | candidate | 记录这是本地 confidence gating，还是有论文支持。 |
| 5 | `IDEA-0002` | 动态局部分支门控与池化 | `idea_tree/ideas/IDEA-0002_dynamic_local_gating/IDEA.md` | unknown | 45 | 45 | needs_adaptation | candidate | 记录来源或理由后，再拆成单变量 trial。 |
| 6 | `IDEA-0007` | 拓扑感知文本属性库 | `idea_tree/ideas/IDEA-0007_text_attribute_reservoir/IDEA.md` | unknown | 45 | 45 | needs_adaptation | candidate | 澄清来源，并决定是否应早于 attribute routing 测试。 |
| 7 | `IDEA-0004` | AG-JEPA 邻居文本变体 | `idea_tree/ideas/IDEA-0004_ag_jepa_neighbor_text/IDEA.md` | unknown | 40 | 40 | direct | candidate | trial 前记录这是本地变体还是论文支持。 |
| 8 | `IDEA-0005` | 反事实负文本 margin | `idea_tree/ideas/IDEA-0005_counterfactual_negative_text/IDEA.md` | unknown | 40 | 40 | direct | candidate | 记录参考来源，或标记为 local heuristic 后再 trial。 |
| 9 | `IDEA-0003` | Cosine-only CrossModal 打分与 anchor loss | `idea_tree/ideas/IDEA-0003_cosine_only_scoring/IDEA.md` | unknown | 35 | 35 | needs_adaptation | candidate | 由于会改变主打分路径，任何 trial 前必须先 review 来源/理由。 |
| 10 | `IDEA-0010` | Seen-unseen 校准 loss | `idea_tree/ideas/IDEA-0010_seen_unseen_calibration/IDEA.md` | unknown | 30 | 30 | needs_adaptation | candidate | 选中 trial 前先找到 GZSL calibration 参考。 |

## 版本感知规则

- 实验顺序使用当前激活版本的分数列。
- 创建新框架版本时，添加新的 `version_scores.vX` 条目。
- 没有重新检查接口适配性前，不要把旧版本分数复制到新版本。
- 高 `global_score` 但低当前分，表示这个想法可能以后有用，不代表现在优先。
