# 实现说明

- `race_model.py`：冻结八句、构造完整 200 类同角色文本 rival 表，并计算三种固定条件。
- `train.py`：仅在 100/50 类不重叠验证上选择 `lambda`；保存选择状态后才加载 official test。
- `aligned` 是候选模块；`no_contrast` 检验收益是否只是重复目标相似度；`wrong_role` 检验角色对齐是否必要。
- 模块无可训练参数，不进行最终 refit，也不使用 gamma。
