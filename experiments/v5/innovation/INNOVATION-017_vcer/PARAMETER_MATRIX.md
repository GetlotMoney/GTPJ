# 参数矩阵：INNOVATION-017_vcer

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：从 PARAMETER_MATRIX.csv 生成

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | VCER-on-X2-formal | innovation | completed | {"batch_size":8,"epochs":50,"preserve_weight":0.05,"rank":16,"unique_causal_weight":1.0,"unique_margin":0.1} | 5 |  | RUN-001 | 验证共享低秩VCER能否在保留X2的同时形成可干预角色证据 | 64.12027046111102 | stop_no_gain |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
