# 参数矩阵：TUNE-001_dynamic_routing_search

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：ATTEMPT-006/WORK_ITEMS.md 中可逐任务核实的 TUNE-001..008；完整配置快照和当次代码提交未保留。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | direction sample h48 w0.475 a0.003 | tune | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"sample","dynamic_hidden":48,"weight_s2v":0.475} | 5 |  | ATTEMPT-006/DR-003 | 搜索方向路由参数 | 74.59 | single_run_valid |  |
| RUN-002 | direction sample h48 w0.525 a0.003 | tune | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"sample","dynamic_hidden":48,"weight_s2v":0.525} | 5 |  | ATTEMPT-006/DR-004 | 搜索方向路由参数 | 74.75 | repeat_candidate |  |
| RUN-003 | direction sample h48 w0.50 a0.001 | tune | completed | {"anchor_lambda":0.001,"dynamic_direction_mode":"sample","dynamic_hidden":48,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-005 | 搜索方向路由参数 | 74.62 | single_run_valid |  |
| RUN-004 | direction sample h48 w0.50 a0.005 | tune | completed | {"anchor_lambda":0.005,"dynamic_direction_mode":"sample","dynamic_hidden":48,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-006 | 搜索方向路由参数 | 74.67 | repeat_candidate |  |
| RUN-005 | direction sample h40 w0.50 a0.003 | tune | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"sample","dynamic_hidden":40,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-007 | 搜索方向路由参数 | 74.59 | single_run_valid |  |
| RUN-006 | direction sample h56 w0.50 a0.003 | tune | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"sample","dynamic_hidden":56,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-008 | 搜索方向路由参数 | 74.14 | single_run_valid |  |
| RUN-007 | direction class h48 w0.50 a0.003 | tune | completed | {"anchor_lambda":0.003,"dynamic_direction_mode":"class","dynamic_hidden":48,"weight_s2v":0.50} | 5 |  | ATTEMPT-006/DR-009 | 比较方向路由模式 | 74.20 | single_run_valid |  |
| RUN-008 | direction sample h48 w0.45 a0.004 | tune | completed | {"anchor_lambda":0.004,"dynamic_direction_mode":"sample","dynamic_hidden":48,"weight_s2v":0.45} | 5 |  | ATTEMPT-006/DR-010 | 搜索方向路由参数 | 74.64 | backup_repeat_candidate |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
