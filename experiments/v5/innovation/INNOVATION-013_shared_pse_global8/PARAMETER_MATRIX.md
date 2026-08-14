# 参数矩阵：INNOVATION-013_shared_pse_global8

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：只加共享PSE的全局分支

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 共享PSE全局分支 | innovation | frozen | {"module":"shared_pse","local_branch":false,"residual_cap":0.35,"max_epochs":100} | 5 |  | RUN-001 | 只加共享PSE并与H=64.164039零号基线比较 |  | pending |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
