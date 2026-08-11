# 参数矩阵：ABLATION-012_pse_attention_validation

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：V5-ABLATION-012-pse-attention-validation-frozen-plan

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | PSE-UNIFORM-seed5-repeat1 | ablation | frozen | {"pse_attention_mode":"uniform","pse_qk_no_decay":false} | 5 |  | V5ABL012-RUN-001 | 判断 learned Q/K 是否比固定均匀注意力有效 |  |  |  |
| RUN-002 | PSE-UNIFORM-seed5-repeat2 | ablation | frozen | {"pse_attention_mode":"uniform","pse_qk_no_decay":false} | 5 | RUN-001 | V5ABL012-RUN-002 | 判断 learned Q/K 是否比固定均匀注意力有效 |  |  |  |
| RUN-003 | PSE-UNIFORM-seed17-repeat1 | ablation | frozen | {"pse_attention_mode":"uniform","pse_qk_no_decay":false} | 17 |  | V5ABL012-RUN-003 | 判断 learned Q/K 是否比固定均匀注意力有效 |  |  |  |
| RUN-004 | PSE-UNIFORM-seed17-repeat2 | ablation | frozen | {"pse_attention_mode":"uniform","pse_qk_no_decay":false} | 17 | RUN-003 | V5ABL012-RUN-004 | 判断 learned Q/K 是否比固定均匀注意力有效 |  |  |  |
| RUN-005 | PSE-NO-QK-DECAY-seed5-repeat1 | ablation | frozen | {"pse_attention_mode":"learned","pse_qk_no_decay":true} | 5 |  | V5ABL012-RUN-005 | 判断 Q/K 清零是否由 Adam 权重衰减造成 |  |  |  |
| RUN-006 | PSE-NO-QK-DECAY-seed5-repeat2 | ablation | frozen | {"pse_attention_mode":"learned","pse_qk_no_decay":true} | 5 | RUN-005 | V5ABL012-RUN-006 | 判断 Q/K 清零是否由 Adam 权重衰减造成 |  |  |  |
| RUN-007 | PSE-NO-QK-DECAY-seed17-repeat1 | ablation | frozen | {"pse_attention_mode":"learned","pse_qk_no_decay":true} | 17 |  | V5ABL012-RUN-007 | 判断 Q/K 清零是否由 Adam 权重衰减造成 |  |  |  |
| RUN-008 | PSE-NO-QK-DECAY-seed17-repeat2 | ablation | frozen | {"pse_attention_mode":"learned","pse_qk_no_decay":true} | 17 | RUN-007 | V5ABL012-RUN-008 | 判断 Q/K 清零是否由 Adam 权重衰减造成 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
