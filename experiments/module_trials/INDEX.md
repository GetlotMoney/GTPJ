# 模块 Trials 索引

当前还没有已启动的模块 trial。

权威 idea 记录放在 `idea_tree/ideas/`。本目录只在某个 idea 被选中并开始代码实现后，
保存 implementation trial 和证据。

| Idea | 源 idea 文件 | Trial 证据目录 | Trial 状态 |
|---|---|---|---|
| `IDEA-0001` | `idea_tree/ideas/IDEA-0001_lastvit_cls/IDEA.md` | `experiments/module_trials/IDEA-0001_lastvit_cls/` | no trial |
| `IDEA-0002` | `idea_tree/ideas/IDEA-0002_dynamic_local_gating/IDEA.md` | `experiments/module_trials/IDEA-0002_dynamic_local_gating/` | no trial |
| `IDEA-0003` | `idea_tree/ideas/IDEA-0003_cosine_only_scoring/IDEA.md` | `experiments/module_trials/IDEA-0003_cosine_only_scoring/` | no trial |
| `IDEA-0004` | `idea_tree/ideas/IDEA-0004_ag_jepa_neighbor_text/IDEA.md` | `experiments/module_trials/IDEA-0004_ag_jepa_neighbor_text/` | no trial |
| `IDEA-0005` | `idea_tree/ideas/IDEA-0005_counterfactual_negative_text/IDEA.md` | `experiments/module_trials/IDEA-0005_counterfactual_negative_text/` | no trial |
| `IDEA-0006` | `idea_tree/ideas/IDEA-0006_geo_attribute_routing/IDEA.md` | `experiments/module_trials/IDEA-0006_geo_attribute_routing/` | no trial |
| `IDEA-0007` | `idea_tree/ideas/IDEA-0007_text_attribute_reservoir/IDEA.md` | `experiments/module_trials/IDEA-0007_text_attribute_reservoir/` | no trial |
| `IDEA-0008` | `idea_tree/ideas/IDEA-0008_attr_patch_ot/IDEA.md` | `experiments/module_trials/IDEA-0008_attr_patch_ot/` | no trial |
| `IDEA-0009` | `idea_tree/ideas/IDEA-0009_uncertainty_msdn_gate/IDEA.md` | `experiments/module_trials/IDEA-0009_uncertainty_msdn_gate/` | no trial |
| `IDEA-0010` | `idea_tree/ideas/IDEA-0010_seen_unseen_calibration/IDEA.md` | `experiments/module_trials/IDEA-0010_seen_unseen_calibration/` | no trial |

启动任何 trial 前：

- 验证或明确记录来源；
- 在 `idea_tree/INDEX.md` 中确认被选版本的分数；
- 通过 workflow helper 创建 `TRIAL-001_<slug>/`；
- 保证 default-off path 等价于选定 base version。
