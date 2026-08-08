# 参数矩阵：ABLATION-005_sgmp_loss_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：CAMP-20260809-v5-ablation100 的 12 个冻结配置；当前未训练

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | MPP-OFF seed=5 repeat=1 | ablation | frozen | {"lambda_mpp":0.0} | 5 |  |  | 验证 MPP 系数贡献 |  |  |  |
| RUN-002 | MPP-OFF seed=5 repeat=2 | ablation | frozen | {"lambda_mpp":0.0} | 5 | RUN-001 |  | 验证 MPP 系数贡献 |  |  |  |
| RUN-003 | MPP-OFF seed=17 repeat=1 | ablation | frozen | {"lambda_mpp":0.0} | 17 |  |  | 验证 MPP 系数贡献 |  |  |  |
| RUN-004 | MPP-OFF seed=17 repeat=2 | ablation | frozen | {"lambda_mpp":0.0} | 17 | RUN-003 |  | 验证 MPP 系数贡献 |  |  |  |
| RUN-005 | NEG-OFF seed=5 repeat=1 | ablation | frozen | {"lambda_neg":0.0} | 5 |  |  | 验证 NEG 系数贡献 |  |  |  |
| RUN-006 | NEG-OFF seed=5 repeat=2 | ablation | frozen | {"lambda_neg":0.0} | 5 | RUN-005 |  | 验证 NEG 系数贡献 |  |  |  |
| RUN-007 | NEG-OFF seed=17 repeat=1 | ablation | frozen | {"lambda_neg":0.0} | 17 |  |  | 验证 NEG 系数贡献 |  |  |  |
| RUN-008 | NEG-OFF seed=17 repeat=2 | ablation | frozen | {"lambda_neg":0.0} | 17 | RUN-007 |  | 验证 NEG 系数贡献 |  |  |  |
| RUN-009 | SGMP-ALL-OFF seed=5 repeat=1 | ablation | frozen | {"lambda_mpp":0.0,"lambda_neg":0.0} | 5 |  |  | 验证两个 SGMP 辅助系数共同贡献 |  |  |  |
| RUN-010 | SGMP-ALL-OFF seed=5 repeat=2 | ablation | frozen | {"lambda_mpp":0.0,"lambda_neg":0.0} | 5 | RUN-009 |  | 验证两个 SGMP 辅助系数共同贡献 |  |  |  |
| RUN-011 | SGMP-ALL-OFF seed=17 repeat=1 | ablation | frozen | {"lambda_mpp":0.0,"lambda_neg":0.0} | 17 |  |  | 验证两个 SGMP 辅助系数共同贡献 |  |  |  |
| RUN-012 | SGMP-ALL-OFF seed=17 repeat=2 | ablation | frozen | {"lambda_mpp":0.0,"lambda_neg":0.0} | 17 | RUN-011 |  | 验证两个 SGMP 辅助系数共同贡献 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
