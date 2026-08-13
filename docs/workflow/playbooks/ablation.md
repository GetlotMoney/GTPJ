# 执行卡：消融 Ablation

用于移除、替换、关闭或隔离既有组件，回答该组件是否有贡献。

## 最短闭环

1. 从 `TEMPLATE.yaml` 锁定的准确母版 commit 建立 `exp/vX/ablation/...` 分支。
2. 在唯一 `PARAMETER_MATRIX.csv` 中为每个对照写一行 `RUN-xxx`，只改变一个待验证因素。
3. 确认 clean worktree、数据/划分、label mapping、class order、logits shape、评估口径、GPU 和输出目录。
4. 使用现有训练入口运行，每个 RUN 独立保存日志、U/S/H/ZS 和必要模型。
5. 回填全部结果并给出 `ablation_supported`、`stopped_ablation_not_supported` 或 `rejected`。

如果需要新增或改写 module、forward、loss、eval、data view 或接口语义，这不是普通消融，必须改走 innovation，并按当前规则完成机器测试和两轮只读审核。

消融不能注册新框架或 Tag。当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`。
