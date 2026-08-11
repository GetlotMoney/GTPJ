# 参数矩阵：ABLATION-006_auxiliary_loss_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：CAMP-20260809-v5-ablation100 的 16 个冻结配置；当前未训练

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | CE-ONLY seed=5 repeat=1 | ablation | frozen | {"lambda_consist":0,"lambda_topo_pearson":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 5 |  |  | 只保留 CE 主损失 |  |  |  |
| RUN-002 | CE-ONLY seed=5 repeat=2 | ablation | frozen | {"lambda_consist":0,"lambda_topo_pearson":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 5 | RUN-001 |  | 只保留 CE 主损失 |  |  |  |
| RUN-003 | CE-ONLY seed=17 repeat=1 | ablation | frozen | {"lambda_consist":0,"lambda_topo_pearson":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 17 |  |  | 只保留 CE 主损失 |  |  |  |
| RUN-004 | CE-ONLY seed=17 repeat=2 | ablation | frozen | {"lambda_consist":0,"lambda_topo_pearson":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 17 | RUN-003 |  | 只保留 CE 主损失 |  |  |  |
| RUN-005 | BMDD-OFF seed=5 repeat=1 | ablation | frozen | {"lambda_bmdd":0} | 5 |  |  | 验证 BMDD 辅助损失贡献 |  |  |  |
| RUN-006 | BMDD-OFF seed=5 repeat=2 | ablation | frozen | {"lambda_bmdd":0} | 5 | RUN-005 |  | 验证 BMDD 辅助损失贡献 |  |  |  |
| RUN-007 | BMDD-OFF seed=17 repeat=1 | ablation | frozen | {"lambda_bmdd":0} | 17 |  |  | 验证 BMDD 辅助损失贡献 |  |  |  |
| RUN-008 | BMDD-OFF seed=17 repeat=2 | ablation | frozen | {"lambda_bmdd":0} | 17 | RUN-007 |  | 验证 BMDD 辅助损失贡献 |  |  |  |
| RUN-009 | CONSIST-OFF seed=5 repeat=1 | ablation | frozen | {"lambda_consist":0} | 5 |  |  | 验证一致性损失贡献 |  |  |  |
| RUN-010 | CONSIST-OFF seed=5 repeat=2 | ablation | frozen | {"lambda_consist":0} | 5 | RUN-009 |  | 验证一致性损失贡献 |  |  |  |
| RUN-011 | CONSIST-OFF seed=17 repeat=1 | ablation | frozen | {"lambda_consist":0} | 17 |  |  | 验证一致性损失贡献 |  |  |  |
| RUN-012 | CONSIST-OFF seed=17 repeat=2 | ablation | frozen | {"lambda_consist":0} | 17 | RUN-011 |  | 验证一致性损失贡献 |  |  |  |
| RUN-013 | LOCAL-AUX-OFF seed=5 repeat=1 | ablation | frozen | {"lambda_consist":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 5 |  |  | 关闭局部辅助损失但保留 topology |  |  |  |
| RUN-014 | LOCAL-AUX-OFF seed=5 repeat=2 | ablation | frozen | {"lambda_consist":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 5 | RUN-013 |  | 关闭局部辅助损失但保留 topology |  |  |  |
| RUN-015 | LOCAL-AUX-OFF seed=17 repeat=1 | ablation | frozen | {"lambda_consist":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 17 |  |  | 关闭局部辅助损失但保留 topology |  |  |  |
| RUN-016 | LOCAL-AUX-OFF seed=17 repeat=2 | ablation | frozen | {"lambda_consist":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0} | 17 | RUN-015 |  | 关闭局部辅助损失但保留 topology |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
