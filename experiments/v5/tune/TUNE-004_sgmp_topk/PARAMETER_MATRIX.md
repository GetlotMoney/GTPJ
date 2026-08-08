# 参数矩阵：TUNE-004_sgmp_topk

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由冻结 CSV 自动生成；结果字段在预跑阶段保持为空。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | SGMP-TOPK16 seed=5 repeat=1 | tune | frozen | {"sgmp_topk":16} | 5 |  |  | 评估 SGMP 采用 top-k 16 的影响 |  |  |  |
| RUN-002 | SGMP-TOPK16 seed=5 repeat=2 | tune | frozen | {"sgmp_topk":16} | 5 | RUN-001 |  | 评估 SGMP 采用 top-k 16 的影响 |  |  |  |
| RUN-003 | SGMP-TOPK16 seed=17 repeat=1 | tune | frozen | {"sgmp_topk":16} | 17 |  |  | 评估 SGMP 采用 top-k 16 的影响 |  |  |  |
| RUN-004 | SGMP-TOPK16 seed=17 repeat=2 | tune | frozen | {"sgmp_topk":16} | 17 | RUN-003 |  | 评估 SGMP 采用 top-k 16 的影响 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
