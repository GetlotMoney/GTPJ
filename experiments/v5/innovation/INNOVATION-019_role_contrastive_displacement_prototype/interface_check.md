# 接口检查

| 项目 | 冻结要求 |
|---|---|
| 文本输入 | `[200,8,768]`，八个角色固定顺序 |
| 图像输入 | 冻结 CLIP CLS `[N,768]` |
| pseudo 候选轴 | 100 pseudo-seen + 50 pseudo-unseen，联合 150 类竞争 |
| 正式候选轴 | 150 seen + 50 unseen，联合 200 类竞争 |
| 输出 | `[N,C]` cosine logits；U/S/ZS 为逐类平均，H 为调和平均 |
| baseline-off | `Up=0` 或 `residual_enabled=false` 精确回到 Mean8 |
| 位移上限 | 每角色 `<=gate*||base||/8`，总位移 `<=gate*||base||` |
| unseen 边界 | 不使用 unseen 图像训练；只使用公开类别文本 |
| official test | checkpoint 保存后加载；每个预声明模型只评估一次 |
