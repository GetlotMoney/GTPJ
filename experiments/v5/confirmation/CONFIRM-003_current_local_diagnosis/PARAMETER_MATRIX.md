# 参数矩阵：CONFIRM-003_current_local_diagnosis

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-CONFIRM-003 最新母版同 seed 三次完整模型运行计划

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | current-full-seed5-repeat1 | confirmation | frozen | {} | 5 |  | V5CONF003-RUN-001 | 最新母版同seed三次基线与互补性诊断 |  |  |  |
| RUN-002 | current-full-seed5-repeat2 | confirmation | frozen | {} | 5 | RUN-001 | V5CONF003-RUN-002 | 最新母版同seed三次基线与互补性诊断 |  |  |  |
| RUN-003 | current-full-seed5-repeat3 | confirmation | frozen | {} | 5 | RUN-001 | V5CONF003-RUN-003 | 最新母版同seed三次基线与互补性诊断 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
