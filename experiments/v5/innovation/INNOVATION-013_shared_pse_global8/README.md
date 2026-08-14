# V5-INNOVATION-013：共享 PSE 全局分支

## 问题

在 `V5-INNOVATION-012/RUN-001` 的 `H=64.164039` 零号基线上，只加入一套共享 PSE，能否提升 GZSL-H？

保留冻结 CLIP CLS 和相同 8 句话；删除 patch、局部分支和全部旧模块。PSE 用同一套句内自注意力、角色权重和有界残差门同时处理 200 个类别，seen 与 unseen 不再走两套规则。残差门从 0 初始化，因此初始分类严格等于零号基线。

训练只使用 seen 训练样本的 CE。epoch 选择只看 seen 训练集内部固定 10% 验证 CE，测试集只在恢复最佳验证 checkpoint 后评估一次。

## 决策

- `ΔH > 0`：保留为候选，检查角色权重和 seen/unseen 原型漂移。
- `ΔH <= 0`：淘汰当前 PSE，不叠加后续模块。
- 单次达到 75 只记 `best_observed_H`，不能写成 confirmed。
