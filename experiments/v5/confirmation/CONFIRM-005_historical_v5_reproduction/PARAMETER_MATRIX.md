# 参数矩阵：CONFIRM-005_historical_v5_reproduction

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-CONFIRM-005 老框架五次独立复现结果

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 老框架原始配置 seed 5 第 1 次 | confirmation | completed | {"code_policy":"historical_exact","local_weight":0.2,"pse_outer_ratio":0.65} | 5 |  | V5-CONFIRM-005-old-framework/RUN-001 | 验证老框架能否恢复 H>=74.40 | 74.2629474857364 | near_miss_not_restored_continue |  |
| RUN-002 | 老框架原始配置 seed 5 第 2 次 | confirmation | completed | {"code_policy":"historical_exact","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | V5-CONFIRM-005-old-framework/RUN-002 | 未命中后按相同条件独立重启 | 74.15075154660323 | near_miss_not_restored_continue |  |
| RUN-003 | 老框架原始配置 seed 5 第 3 次 | confirmation | completed | {"code_policy":"historical_exact","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | V5-CONFIRM-005-old-framework/RUN-003 | 未命中后按相同条件独立重启 | 74.15141093235394 | near_miss_not_restored_continue |  |
| RUN-004 | 老框架原始配置 seed 5 第 4 次 | confirmation | completed | {"code_policy":"historical_exact","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | V5-CONFIRM-005-old-framework/RUN-004 | 未命中后按相同条件独立重启 | 74.32302720855894 | near_miss_not_restored_continue |  |
| RUN-005 | 老框架原始配置 seed 5 第 5 次 | confirmation | completed | {"code_policy":"historical_exact","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | V5-CONFIRM-005-old-framework/RUN-005 | 第五次同条件独立重启并按硬上限收口 | 74.27493079185446 | near_miss_not_restored_hard_cap_reached |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
