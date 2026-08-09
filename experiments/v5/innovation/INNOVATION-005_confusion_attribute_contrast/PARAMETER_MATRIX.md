# 参数矩阵：INNOVATION-005_confusion_attribute_contrast

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5 局部互补性三种子稳定性检查

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 混淆难负类 seed 5 | innovation | frozen | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 5 |  |  | seed 5 预注册初筛 |  |  |  |
| RUN-002 | 混淆难负类 seed 17 | innovation | frozen | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 17 |  |  | 多种子稳定性检查；不是复现确认 |  |  |  |
| RUN-003 | 混淆难负类 seed 29 | innovation | frozen | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 29 |  |  | 多种子稳定性检查；不是复现确认 |  |  |  |
| RUN-004 | 混淆难负类 seed 17 基础设施重试 | innovation | frozen | {"ablation_disable_fgvd_geometry":true,"lambda_local_ce":0.1,"lambda_confusion_contrast":0.1,"confusion_topk":5,"confusion_margin":0.1} | 17 | RUN-002 |  | Windows 日志锁中断后的同配置重试 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
