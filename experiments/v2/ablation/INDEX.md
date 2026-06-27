# GTPJ-v2 Ablation 索引

ID 规范：`ABL-001_slug`；目录：`experiments/v2/ablation/ABL-001_slug/`。

当前还没有 v2 version-level ablation 运行。

优先建议的 v2 消融方向：

- 关闭 `use_clip_a_self`，确认 switch-off path 是否回到 v1 文本原型行为；
- 改变 `clip_a_self_outer_ratio`，量化二级残差对 U/S/H 的影响；
- 设置 `clip_a_self_apply_unseen=true`，仅作为风险消融，不作为默认训练语义。
