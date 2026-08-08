# 参数矩阵：INNOVATION-002_scale_consistent_fusion

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-INNOVATION-002 预注册十行计划

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | legacy seed 5 repeat 1 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 5 |  |  | 比较 legacy 与 scale_consistent 的同 seed 配对结果 |  |  |  |
| RUN-002 | scale-consistent seed 5 repeat 1 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 5 |  |  | 比较 legacy 与 scale_consistent 的同 seed 配对结果 |  |  |  |
| RUN-003 | legacy seed 5 repeat 2 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 5 | RUN-001 |  | 比较 legacy 与 scale_consistent 的同 seed 配对结果 |  |  |  |
| RUN-004 | scale-consistent seed 5 repeat 2 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 5 | RUN-002 |  | 比较 legacy 与 scale_consistent 的同 seed 配对结果 |  |  |  |
| RUN-005 | legacy seed 5 repeat 3 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 5 | RUN-001 |  | 比较 legacy 与 scale_consistent 的同 seed 配对结果 |  |  |  |
| RUN-006 | scale-consistent seed 5 repeat 3 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 5 | RUN-002 |  | 比较 legacy 与 scale_consistent 的同 seed 配对结果 |  |  |  |
| RUN-007 | legacy seed 17 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 17 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | blocked_by_stage1_gate |  |
| RUN-008 | scale-consistent seed 17 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 17 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | blocked_by_stage1_gate |  |
| RUN-009 | legacy seed 29 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 29 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | blocked_by_stage1_gate |  |
| RUN-010 | scale-consistent seed 29 | innovation | planned | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 29 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | blocked_by_stage1_gate |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
