# 参数矩阵：INNOVATION-016_te_pse_vsc

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：从 PARAMETER_MATRIX.csv 生成

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | te-pse-vsc-seed5 | innovation | frozen | {"parent_te_pse_commit":"b7f060afdd6d42baeee25b4d3068389085d88286","vsc_weight":0.1,"vsc_direction":"symmetric","centroid_source":"seen_train_90pct_only","inference_change":false} | 5 |  | RUN-001 | 验证简单双向视觉语义中心一致性是否改善TE-PSE的raw GZSL H |  | planned |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
