# 参数矩阵：INNOVATION-001_dynamic_routing

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：ATTEMPT-006/WORK_ITEMS.md 中可逐任务核实的 INNOV-001..002；其余旧批次只在 LEGACY_ATTEMPT_MAP.md 显示摘要。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | local sample + direction sample | innovation | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"sample","dynamic_hidden":48,"dynamic_local_weight":0.06,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-001 | 验证局部采样与方向采样组合 | 73.62 | stop_no_gain |  |
| RUN-002 | direction sample + PSE class | innovation | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"sample","dynamic_hidden":48,"pse_outer_ratio":0.55,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-002 | 验证方向采样与 PSE 类别分支组合 | 73.63 | stop_no_gain |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
