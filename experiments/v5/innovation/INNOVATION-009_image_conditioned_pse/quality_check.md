# V5-INNOVATION-009 质量检查

结论：`RUN-002` 训练与结果证据完整，可作为单次筛选结果；方法决定为 `reject`，不具备 confirmation 或 promotion 资格。

## 已核对

- 冻结训练提交：`28c644ea8ec7a4b34f660fe492bd1159ded385ec`。
- 训练进程完成 50 epoch，退出码为 `0`。
- 开始收据、结束收据和封口日志的 PID、命令 SHA、时间及返回码一致。
- 封口日志 SHA-256：`bdcc73e182f2c4c0837221269c7075de1f86e303720f4ef27a2c48b08d9035de`。
- 完整 `U/S/H/ZS`、最佳 epoch、耗时、模型大小、显存和句子权重诊断来自同一 `final_metrics.json` 与最佳模型；最终指标文件 SHA-256 为 `6fd7aa5faf0e3c7527217c736738b7fa63b122b69ebbea4c00f5e512cf12c61e`。
- 结束收据 SHA-256 为 `0bab5ce215f9256d0907b1780680caf029e46f2973d649bcb614467ce202aba7`，由开始/结束时间推得总墙钟时间为 578 秒。
- 最佳模型 SHA-256：`f49be7644e9195c6dfd3f9327b4bed2bdfd598fc2a0c91af0f5c2f1082f1d36f`。
- `RUN-001` 的设备错误及失败日志保留，`RUN-002` 使用独立目录，没有覆盖历史证据。

## 科学边界

- 只有 seed=5 的一次成功运行，不能估计重复训练波动。
- `H=59.41` 比 V5 五次重复均值 `74.44` 低 `15.03` 个点，足以在候选筛选阶段判定不继续投入复跑，但不能据此证明所有图像条件选句方法都无效。
- 本结果不得登记为 `keep`、best、confirmed 或 promotion evidence。
