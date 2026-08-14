# 参数矩阵：INNOVATION-015_te_pse

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：owner 2026-08-15 TE-PSE 候选；MODEL-V5-TEMPLATE-V2；GPT-5.6 八句干净全局基线。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | te-pse-role-rival-evidence-seed5 | innovation | frozen | {"text_source":"gpt56_8sent","score_path":"clip_cls_x_te_pse_role_rival_evidence","evidence_roles":7,"evidence_cap":0.5,"evidence_init":0.1,"temperature":0.05,"trainable_parameters":1} | 5 |  | RUN-001 | 验证同角色最强rival的可迁移加性证据是否提高raw GZSL H |  | planned |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
