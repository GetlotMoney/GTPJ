# V5-TUNE-002 服务器启动计划

## 固定分配

- 物理 GPU 0，由外层队列设置 `CUDA_VISIBLE_DEVICES=0`。
- 进程内设备继续使用每份配置中的逻辑 `cuda:0`。
- 统一 campaign：`CAMP-20260809-v5-ablation100`。
- 固定顺序为 `RUN-001` 到 `RUN-016`；不得根据中途分数改变参数或跳过复跑。
- 每个 RUN 使用独立且不存在的外部输出目录，至少保存 `training.log`、最终指标和需要保留的最佳模型。

## 启动边界

当前 `strict-3` 状态仍为 `review_pending`，本次任务不训练。审核完成并重新确认 clean、代码提交、配置 hash、数据身份和 GPU 后，才允许由统一 campaign 启动；禁止手工正式启动。
