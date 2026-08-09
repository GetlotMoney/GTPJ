# 参数矩阵：INNOVATION-002_scale_consistent_fusion

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-INNOVATION-002：Stage 1 六行完成；Stage 2 因门未通过未启动

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | legacy seed 5 repeat 1 | innovation | completed | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 5 |  | RUN-001 | 比较 legacy 与 scale_consistent 的同 seed 配对结果 | 74.14438265496587 | legacy_reference |  |
| RUN-002 | scale-consistent seed 5 repeat 1 | innovation | completed | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 5 |  | RUN-002 | 比较 legacy 与 scale_consistent 的同 seed 配对结果 | 70.95346445779093 | reject_scale_consistent_beta_0_05 |  |
| RUN-003 | legacy seed 5 repeat 2 | innovation | completed | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 5 | RUN-001 | RUN-003 | 比较 legacy 与 scale_consistent 的同 seed 配对结果 | 74.2022181394866 | legacy_reference |  |
| RUN-004 | scale-consistent seed 5 repeat 2 | innovation | completed | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 5 | RUN-002 | RUN-004 | 比较 legacy 与 scale_consistent 的同 seed 配对结果 | 71.28466674908928 | reject_scale_consistent_beta_0_05 |  |
| RUN-005 | legacy seed 5 repeat 3 | innovation | completed | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 5 | RUN-001 | RUN-005 | 比较 legacy 与 scale_consistent 的同 seed 配对结果 | 74.04299674877775 | legacy_reference |  |
| RUN-006 | scale-consistent seed 5 repeat 3 | innovation | completed | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 5 | RUN-002 | RUN-006 | 比较 legacy 与 scale_consistent 的同 seed 配对结果 | 71.06499083042776 | reject_scale_consistent_beta_0_05 |  |
| RUN-007 | legacy seed 17 | innovation | skipped | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 17 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | stage1_gate_failed_not_started |  |
| RUN-008 | scale-consistent seed 17 | innovation | skipped | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 17 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | stage1_gate_failed_not_started |  |
| RUN-009 | legacy seed 29 | innovation | skipped | {"fusion_beta":0.05,"fusion_mode":"legacy"} | 29 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | stage1_gate_failed_not_started |  |
| RUN-010 | scale-consistent seed 29 | innovation | skipped | {"fusion_beta":0.05,"fusion_mode":"scale_consistent"} | 29 |  |  | 在 stage1 通过后检查跨 seed 稳健性 |  | stage1_gate_failed_not_started |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
