# 参数矩阵：ABLATION-001_local_branch_effect

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：codex/attempt019-local-ablation 冻结的 15 个 DR-001..DR-015 计划；全部仍是 planned，未启动训练。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | full baseline repeat 1 | ablation | planned | {"local_weight":0.2,"use_dynamic_routing":false} | 5 |  | DR-001 | measure local branch contribution |  |  |  |
| RUN-002 | full baseline repeat 2 | ablation | planned | {"local_weight":0.2,"use_dynamic_routing":false} | 5 | RUN-001 | DR-002 | measure local branch contribution |  |  |  |
| RUN-003 | full baseline repeat 3 | ablation | planned | {"local_weight":0.2,"use_dynamic_routing":false} | 5 | RUN-001 | DR-003 | measure local branch contribution |  |  |  |
| RUN-004 | local score disabled repeat 1 | ablation | planned | {"local_weight":0.0,"use_dynamic_routing":false} | 5 |  | DR-004 | measure local branch contribution |  |  |  |
| RUN-005 | local score disabled repeat 2 | ablation | planned | {"local_weight":0.0,"use_dynamic_routing":false} | 5 | RUN-004 | DR-005 | measure local branch contribution |  |  |  |
| RUN-006 | local score disabled repeat 3 | ablation | planned | {"local_weight":0.0,"use_dynamic_routing":false} | 5 | RUN-004 | DR-006 | measure local branch contribution |  |  |  |
| RUN-007 | local weight 0.1 repeat 1 | ablation | planned | {"local_weight":0.1,"use_dynamic_routing":false} | 5 |  | DR-007 | measure local branch contribution |  |  |  |
| RUN-008 | local weight 0.1 repeat 2 | ablation | planned | {"local_weight":0.1,"use_dynamic_routing":false} | 5 | RUN-007 | DR-008 | measure local branch contribution |  |  |  |
| RUN-009 | local weight 0.1 repeat 3 | ablation | planned | {"local_weight":0.1,"use_dynamic_routing":false} | 5 | RUN-007 | DR-009 | measure local branch contribution |  |  |  |
| RUN-010 | local weight 0.3 repeat 1 | ablation | planned | {"local_weight":0.3,"use_dynamic_routing":false} | 5 |  | DR-010 | measure local branch contribution |  |  |  |
| RUN-011 | local weight 0.3 repeat 2 | ablation | planned | {"local_weight":0.3,"use_dynamic_routing":false} | 5 | RUN-010 | DR-011 | measure local branch contribution |  |  |  |
| RUN-012 | local weight 0.3 repeat 3 | ablation | planned | {"local_weight":0.3,"use_dynamic_routing":false} | 5 | RUN-010 | DR-012 | measure local branch contribution |  |  |  |
| RUN-013 | full local subsystem disabled repeat 1 | ablation | planned | {"lambda_bmdd":0.0,"lambda_consist":0.0,"lambda_mpp":0.0,"lambda_neg":0.0,"local_weight":0.0,"use_dynamic_routing":false,"use_sgmp":false} | 5 |  | DR-013 | measure local branch contribution |  |  |  |
| RUN-014 | full local subsystem disabled repeat 2 | ablation | planned | {"lambda_bmdd":0.0,"lambda_consist":0.0,"lambda_mpp":0.0,"lambda_neg":0.0,"local_weight":0.0,"use_dynamic_routing":false,"use_sgmp":false} | 5 | RUN-013 | DR-014 | measure local branch contribution |  |  |  |
| RUN-015 | full local subsystem disabled repeat 3 | ablation | planned | {"lambda_bmdd":0.0,"lambda_consist":0.0,"lambda_mpp":0.0,"lambda_neg":0.0,"local_weight":0.0,"use_dynamic_routing":false,"use_sgmp":false} | 5 | RUN-013 | DR-015 | measure local branch contribution |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
