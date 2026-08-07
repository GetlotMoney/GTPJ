# 接口检查

## 输入与输出

- 输入仍为 `[B（图片数量）, 577（1 个 CLS 加 576 个局部块）, D（特征维度）]`；
- 只读取第 0 个 CLS，局部块值不影响训练或评估输出；
- 训练 `clip_S_pp` 为 `[B, C_seen（已见类数量）]`；
- 评估 `clip_S_pp` 为 `[B, C_all（全部类别数量）]`；
- `global_logits` 和 `final_logits` 均为 `[B, C_all]`，两者逐元素相同；
- seen/unseen 类别编号、类别顺序和标签映射未修改。

## 损失

总损失严格为：

`loss = loss_ce + lambda_topo_pearson * loss_topo`

返回字段只有 `loss`、`loss_ce`、`loss_topo`。没有局部分支专属损失的零值占位，避免日志让人误以为这些模块仍存在。

## 机器证据

- 实验分支：25 项相关测试全部通过，无跳过；其中 17 项继续验证完整 V5 母版路径，5 项验证无局部路径，3 项验证双 GPU 队列和固定入口；
- 冻结母版工作区：17 项母版测试全部通过，无跳过；
- 新增 5 项行为测试全部通过；
- `model/V5GlobalOnly.py`、`train_V5_ABLATION_001_CUB.py`、两份服务器执行器和新测试均通过 `py_compile`；
- 固定 CLS、把 576 个局部块替换为另一组随机值并放大 1000 倍，训练与评估 logits 仍逐元素完全一致；
- 反向传播后 CLS 梯度非零，576 个局部块梯度总和为 0。

## 当前决定

接口检查结果：`allow_for_code_review`。正式 Runner 仍需 `strict-3` 审核、运行时门和运行前冻结提交。
