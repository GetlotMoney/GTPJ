# 参数矩阵：ABLATION-003_icsa_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由 new-experiment 生成；该草稿必须填写并通过校验后才能用于正式运行。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 关闭 ICSA seed 5 | ablation | frozen | {"ablation_disable_icsa": true} | 5 |  |  | 验证 ICSA 对 seed 5 的独立影响 |  |  |  |
| RUN-002 | 关闭 ICSA seed 17 | ablation | frozen | {"ablation_disable_icsa": true} | 17 |  |  | 验证 ICSA 对 seed 17 的独立影响 |  |  |  |
| RUN-003 | 关闭 ICSA seed 29 | ablation | frozen | {"ablation_disable_icsa": true} | 29 |  |  | 验证 ICSA 对 seed 29 的独立影响 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
