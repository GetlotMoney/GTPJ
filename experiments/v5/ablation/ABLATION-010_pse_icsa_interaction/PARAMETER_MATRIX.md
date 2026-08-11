# 参数矩阵：ABLATION-010_pse_icsa_interaction

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由四份冻结配置逐行生成；PSE 关闭后显式关闭失去梯度作用的 topology

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 关闭 PSE 与 ICSA seed 5 第1次 | ablation | frozen | {"ablation_disable_icsa": true, "ablation_disable_pse": true, "lambda_topo_pearson": 0.0} | 5 |  |  | 种子 5 第1次：验证同时关闭 PSE 与 ICSA 的影响 |  |  |  |
| RUN-002 | 关闭 PSE 与 ICSA seed 5 第2次 | ablation | frozen | {"ablation_disable_icsa": true, "ablation_disable_pse": true, "lambda_topo_pearson": 0.0} | 5 | RUN-001 |  | 种子 5 第2次：排除单次训练偶然性 |  |  |  |
| RUN-003 | 关闭 PSE 与 ICSA seed 17 第1次 | ablation | frozen | {"ablation_disable_icsa": true, "ablation_disable_pse": true, "lambda_topo_pearson": 0.0} | 17 |  |  | 种子 17 第1次：验证同时关闭 PSE 与 ICSA 的影响 |  |  |  |
| RUN-004 | 关闭 PSE 与 ICSA seed 17 第2次 | ablation | frozen | {"ablation_disable_icsa": true, "ablation_disable_pse": true, "lambda_topo_pearson": 0.0} | 17 | RUN-003 |  | 种子 17 第2次：排除单次训练偶然性 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
