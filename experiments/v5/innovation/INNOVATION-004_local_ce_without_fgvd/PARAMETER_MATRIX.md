# 参数矩阵：INNOVATION-004_local_ce_without_fgvd

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-INNOVATION-004 真实运行结果

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 局部 CE seed 5 | innovation | completed | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1} | 5 |  | V5-INNOVATION-004/RUN-001 | seed 5 预注册初筛 | 74.17225723328802 | reject_no_clear_gain |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
