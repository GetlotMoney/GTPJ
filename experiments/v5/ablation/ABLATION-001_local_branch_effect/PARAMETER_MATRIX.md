# 参数矩阵：ABLATION-001_local_branch_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：`MODEL-V5-TEMPLATE-V1@2f5fa5e` 重新绑定的 15 行计划；旧 `codex/attempt019-local-ablation#ATTEMPT-019` 仅供回查。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | 完整母版复跑 1 | ablation | planned | {} | 5 |  |  | 建立新母版基线；旧计划 DR-001 |  |  |  |
| RUN-002 | 完整母版复跑 2 | ablation | planned | {} | 5 | RUN-001 |  | 建立新母版基线；旧计划 DR-002 |  |  |  |
| RUN-003 | 完整母版复跑 3 | ablation | planned | {} | 5 | RUN-001 |  | 建立新母版基线；旧计划 DR-003 |  |  |  |
| RUN-004 | 只关闭局部分数 1 | ablation | planned | {"local_weight":0.0} | 5 |  |  | 只测融合分数贡献；旧计划 DR-004 |  |  |  |
| RUN-005 | 只关闭局部分数 2 | ablation | planned | {"local_weight":0.0} | 5 | RUN-004 |  | 只测融合分数贡献；旧计划 DR-005 |  |  |  |
| RUN-006 | 只关闭局部分数 3 | ablation | planned | {"local_weight":0.0} | 5 | RUN-004 |  | 只测融合分数贡献；旧计划 DR-006 |  |  |  |
| RUN-007 | 局部权重 0.1 复跑 1 | ablation | planned | {"local_weight":0.1} | 5 |  |  | 局部分数权重敏感性；旧计划 DR-007 |  |  |  |
| RUN-008 | 局部权重 0.1 复跑 2 | ablation | planned | {"local_weight":0.1} | 5 | RUN-007 |  | 局部分数权重敏感性；旧计划 DR-008 |  |  |  |
| RUN-009 | 局部权重 0.1 复跑 3 | ablation | planned | {"local_weight":0.1} | 5 | RUN-007 |  | 局部分数权重敏感性；旧计划 DR-009 |  |  |  |
| RUN-010 | 局部权重 0.3 复跑 1 | ablation | planned | {"local_weight":0.3} | 5 |  |  | 局部分数权重敏感性；旧计划 DR-010 |  |  |  |
| RUN-011 | 局部权重 0.3 复跑 2 | ablation | planned | {"local_weight":0.3} | 5 | RUN-010 |  | 局部分数权重敏感性；旧计划 DR-011 |  |  |  |
| RUN-012 | 局部权重 0.3 复跑 3 | ablation | planned | {"local_weight":0.3} | 5 | RUN-010 |  | 局部分数权重敏感性；旧计划 DR-012 |  |  |  |
| RUN-013 | 完全移除局部分支 1 | ablation | planned | {"experiment_variant":"global_only"} | 5 |  |  | 代码级移除 FGVD/BVSA/ICSA/SGMP；旧计划 DR-013 |  |  |  |
| RUN-014 | 完全移除局部分支 2 | ablation | planned | {"experiment_variant":"global_only"} | 5 | RUN-013 |  | 代码级移除 FGVD/BVSA/ICSA/SGMP；旧计划 DR-014 |  |  |  |
| RUN-015 | 完全移除局部分支 3 | ablation | planned | {"experiment_variant":"global_only"} | 5 | RUN-013 |  | 代码级移除 FGVD/BVSA/ICSA/SGMP；旧计划 DR-015 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
