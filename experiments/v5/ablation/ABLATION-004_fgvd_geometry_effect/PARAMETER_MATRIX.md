# 参数矩阵：ABLATION-004_fgvd_geometry_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由四份冻结配置逐行生成；唯一变化是旁路 FGVD 几何编码。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 关闭 FGVD 几何编码 seed 5 第1次 | ablation | frozen | {"ablation_disable_fgvd_geometry": true} | 5 |  |  | 种子 5 第1次：验证 FGVD 几何编码的独立贡献 |  |  |  |
| RUN-002 | 关闭 FGVD 几何编码 seed 5 第2次 | ablation | frozen | {"ablation_disable_fgvd_geometry": true} | 5 | RUN-001 |  | 种子 5 第2次：排除单次训练偶然性 |  |  |  |
| RUN-003 | 关闭 FGVD 几何编码 seed 17 第1次 | ablation | frozen | {"ablation_disable_fgvd_geometry": true} | 17 |  |  | 种子 17 第1次：验证 FGVD 几何编码的独立贡献 |  |  |  |
| RUN-004 | 关闭 FGVD 几何编码 seed 17 第2次 | ablation | frozen | {"ablation_disable_fgvd_geometry": true} | 17 | RUN-003 |  | 种子 17 第2次：排除单次训练偶然性 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
