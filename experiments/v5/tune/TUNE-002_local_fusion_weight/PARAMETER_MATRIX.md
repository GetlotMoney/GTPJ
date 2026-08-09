# 参数矩阵：TUNE-002_local_fusion_weight

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：由 16 份冻结配置逐行生成；每行只改变 local_weight 和运行种子。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | LW-005-seed-5-repeat-1 | tune | frozen | {"local_weight":0.05} | 5 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-002 | LW-005-seed-5-repeat-2 | tune | frozen | {"local_weight":0.05} | 5 | RUN-001 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-003 | LW-005-seed-17-repeat-1 | tune | frozen | {"local_weight":0.05} | 17 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-004 | LW-005-seed-17-repeat-2 | tune | frozen | {"local_weight":0.05} | 17 | RUN-003 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-005 | LW-010-seed-5-repeat-1 | tune | frozen | {"local_weight":0.1} | 5 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-006 | LW-010-seed-5-repeat-2 | tune | frozen | {"local_weight":0.1} | 5 | RUN-005 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-007 | LW-010-seed-17-repeat-1 | tune | frozen | {"local_weight":0.1} | 17 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-008 | LW-010-seed-17-repeat-2 | tune | frozen | {"local_weight":0.1} | 17 | RUN-007 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-009 | LW-030-seed-5-repeat-1 | tune | frozen | {"local_weight":0.3} | 5 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-010 | LW-030-seed-5-repeat-2 | tune | frozen | {"local_weight":0.3} | 5 | RUN-009 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-011 | LW-030-seed-17-repeat-1 | tune | frozen | {"local_weight":0.3} | 17 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-012 | LW-030-seed-17-repeat-2 | tune | frozen | {"local_weight":0.3} | 17 | RUN-011 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-013 | LW-040-seed-5-repeat-1 | tune | frozen | {"local_weight":0.4} | 5 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-014 | LW-040-seed-5-repeat-2 | tune | frozen | {"local_weight":0.4} | 5 | RUN-013 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-015 | LW-040-seed-17-repeat-1 | tune | frozen | {"local_weight":0.4} | 17 |  |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |
| RUN-016 | LW-040-seed-17-repeat-2 | tune | frozen | {"local_weight":0.4} | 17 | RUN-015 |  | 局部融合权重筛查；非 confirmation 证据 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
