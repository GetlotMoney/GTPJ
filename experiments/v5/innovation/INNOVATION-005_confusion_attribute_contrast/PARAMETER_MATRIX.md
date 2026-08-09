# 参数矩阵：INNOVATION-005_confusion_attribute_contrast

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-INNOVATION-005 三种子与失败重跑结果

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 混淆难负类 seed 5 | innovation | completed | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 5 |  | V5-INNOVATION-005/RUN-001 | seed 5 预注册初筛 | 74.26570653779179 | best_diagnostic_not_promoted |  |
| RUN-002 | 混淆难负类 seed 17 | innovation | failed | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 17 |  | V5-INNOVATION-005/RUN-002 | 多种子稳定性检查；不是复现确认 |  | failed_io_lock_retried_as_RUN-004 |  |
| RUN-003 | 混淆难负类 seed 29 | innovation | completed | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 29 |  | V5-INNOVATION-005/RUN-003 | 多种子稳定性检查；不是复现确认 | 74.19233283672965 | stable_diagnostic_not_promoted |  |
| RUN-004 | 混淆难负类 seed 17 基础设施重试 | innovation | completed | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 17 | RUN-002 | V5-INNOVATION-005/RUN-004 | Windows 日志锁中断并修复保存逻辑后的同科学配置重跑 | 74.07286336138624 | stable_diagnostic_not_promoted |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
