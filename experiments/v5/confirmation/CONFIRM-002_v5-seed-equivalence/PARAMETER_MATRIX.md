# 参数矩阵：CONFIRM-002_v5-seed-equivalence

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由 new-experiment 生成；该草稿必须填写并通过校验后才能用于正式运行。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 修复版V5同seed复跑1 | confirmation | draft | {"seed_initialization_compatibility":"historical_v5_rng_position"} | 5 |  | V5CONF002-R1-RUN-001 | 确认修复版V5能否回到老V5同seed训练起点 |  |  |  |
| RUN-002 | 修复版V5同seed复跑2 | confirmation | draft | {"seed_initialization_compatibility":"historical_v5_rng_position"} | 5 | RUN-001 | V5CONF002-R1-RUN-002 | 完成五次分布并报告U/S/H/ZS与均值范围 |  |  |  |
| RUN-003 | 修复版V5同seed复跑3 | confirmation | draft | {"seed_initialization_compatibility":"historical_v5_rng_position"} | 5 | RUN-001 | V5CONF002-R1-RUN-003 | 完成五次分布并报告U/S/H/ZS与均值范围 |  |  |  |
| RUN-004 | 修复版V5同seed复跑4 | confirmation | draft | {"seed_initialization_compatibility":"historical_v5_rng_position"} | 5 | RUN-001 | V5CONF002-R1-RUN-004 | 完成五次分布并报告U/S/H/ZS与均值范围 |  |  |  |
| RUN-005 | 修复版V5同seed复跑5 | confirmation | draft | {"seed_initialization_compatibility":"historical_v5_rng_position"} | 5 | RUN-001 | V5CONF002-R1-RUN-005 | 完成五次分布并报告U/S/H/ZS与均值范围 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
