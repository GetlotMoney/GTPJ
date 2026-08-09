# 参数矩阵：ABLATION-011_current_global_only

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-ABLATION-011-global-only-frozen-plan

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | current-global-only-seed5-repeat1 | ablation | completed | {"score_path":"global_only"} | 5 |  | V5ABL011-RUN-001 | 当前 V5 global-only 同 seed 三次独立运行 | 74.11180679506354 | diagnostic_only |  |
| RUN-002 | current-global-only-seed5-repeat2 | ablation | completed | {"score_path":"global_only"} | 5 | RUN-001 | V5ABL011-RUN-002 | 当前 V5 global-only 同 seed 三次独立运行 | 74.11180679506354 | diagnostic_only |  |
| RUN-003 | current-global-only-seed5-repeat3 | ablation | completed | {"score_path":"global_only"} | 5 | RUN-001 | V5ABL011-RUN-003 | 当前 V5 global-only 同 seed 三次独立运行 | 74.11180679506354 | diagnostic_only |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
