# 参数矩阵：CONFIRM-004_latest_code_best_framework

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-CONFIRM-004 最新代码完整框架复现预跑计划

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 最新代码完整框架复现 seed 5 | confirmation | frozen | {"code_policy":"latest","ablation_disable_fgvd_geometry":false,"lambda_local_ce":0.0,"lambda_confusion_contrast":0.0,"lambda_crop_distill":0.0} | 5 |  | V5-CONFIRM-004/RUN-001 | 验证最新代码能否恢复历史最好框架约 74.4 H |  | pending |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
