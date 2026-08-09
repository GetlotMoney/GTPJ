# V5-INNOVATION-009 结果

状态：`completed_not_keep`。`RUN-001` 因评估设备错误失败；`RUN-002` 保持同一 seed 和参数重跑，完整完成 50 epoch。

## 最终结果

| Run | Seed | 最佳 epoch | U | S | H | ZS | 训练耗时 | 总墙钟时间 | 最佳模型文件 | 决定 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `RUN-002` | 5 | 1 | 47.921973 | 78.128189 | 59.405826 | 76.428151 | 563.186 秒 | 578 秒 | 99,797,346 bytes（95.17 MiB） | `reject` |

- 代码提交：`28c644ea8ec7a4b34f660fe492bd1159ded385ec`
- 数据清单 SHA-256：`6d71da3b580a6fabb29111d34b6d64d08f2aca93f8fe02ac8795972427ebb983`
- 参数量 / 可训练参数量：`14,324,741 / 12,942,341`
- 模型状态大小：`99,766,292 bytes`；最佳模型 SHA-256：`f49be7644e9195c6dfd3f9327b4bed2bdfd598fc2a0c91af0f5c2f1082f1d36f`
- CUDA 峰值：allocated `1,710,264,320 bytes`（1631.04 MiB），reserved `2,373,976,064 bytes`（2264 MiB）。
- 相比 V5 五次重复均值 `H=74.44`，本次低 `15.03` 个点；差距远大于是否值得追加重复训练的边界，因此停止在单次筛选，不进入 promotion。

## 最佳轮诊断

8 个槽位按“喙、头部、身体羽毛、翅膀、尾巴、腿部、整体、独特判别特征”的平均权重为：

```text
[0.128400, 0.121776, 0.125144, 0.126607,
 0.128832, 0.126550, 0.116684, 0.126007]
```

- 均匀权重是 `0.125`；记录的均匀偏差为 `0.033313`，各槽位仍很接近均匀分配。
- 图像条件原型与均匀平均原型的 cosine 为 `0.994662`，两者差距仅 `1-cos=0.005338`。
- 全局 / 局部 / 最终分数绝对均值为 `1.237527 / 0.349566 / 1.267783`。

这说明最佳轮的平均句权接近均匀，没有形成强偏好，产生的类别原型也与均匀平均非常接近；同时最终 H 明显低于基线。就这版实现而言，“只让全局图像选择 8 句话”不够。

## RUN-001 失败记录

- 代码提交：`2aed5d6922887e591698ea4151fd51bca63ea307`
- 已完成：真实缓存加载与第 1 个 epoch 的全部训练步。
- 失败位置：首次评估的 ZS 类别索引。
- 原因：评估 logits 已在 CPU，但 `unseenclasses` 仍在 CUDA，PyTorch 拒绝跨设备索引。
- 指标：未完成首次完整 U/S/H/ZS 评估，因此不记录结果数值。
- 证据：`/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/innovation/V5-INNOVATION-009/RUN-001/training.log`
- 处理：保留失败记录；修复设备统一后使用新的运行目录重跑，不覆盖本目录。

## 结论边界

- `RUN-002` 是有效单次正式运行，可用于淘汰这个候选实现。
- 本实验没有做同配置多次独立重复，不能估计方差，也不能把结果写成稳定性或 confirmation 证据。
- 原始日志、收据、最佳模型和最终 JSON 均保存在 Warehouse 的独立 `RUN-001` / `RUN-002` 目录，失败记录没有被覆盖。

## 证据哈希

| 文件 | SHA-256 |
|---|---|
| helper 封口 `training.log` | `bdcc73e182f2c4c0837221269c7075de1f86e303720f4ef27a2c48b08d9035de` |
| `run_start_receipt.json` | `1fcb64aed24c477c91cbc699d652878ba230b4df77678f05e0a9a09078931bcd` |
| `run_start_receipt.finish.json` | `0bab5ce215f9256d0907b1780680caf029e46f2973d649bcb614467ce202aba7` |
| `artifacts/final_metrics.json` | `6fd7aa5faf0e3c7527217c736738b7fa63b122b69ebbea4c00f5e512cf12c61e` |
| `artifacts/model_training.log` | `63c5f95e7f4cf3fb076e97d215c41b777cad5230646e67411526728bfe9eef46` |
| `artifacts/model_best.pth` | `f49be7644e9195c6dfd3f9327b4bed2bdfd598fc2a0c91af0f5c2f1082f1d36f` |
