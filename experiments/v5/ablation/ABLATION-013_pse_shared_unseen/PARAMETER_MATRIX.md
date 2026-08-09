# 参数矩阵：ABLATION-013_pse_shared_unseen

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：从 PARAMETER_MATRIX.csv 生成

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | PSE-SEEN-ONLY-seed5-repeat1 | ablation | frozen | {"pse_apply_unseen":false} | 5 |  | V5ABL013-RUN-001 | 当前已见类使用 PSE 而未见类直接平均 |  |  |  |
| RUN-002 | PSE-SEEN-ONLY-seed5-repeat2 | ablation | frozen | {"pse_apply_unseen":false} | 5 | RUN-001 | V5ABL013-RUN-002 | 当前已见类使用 PSE 而未见类直接平均 |  |  |  |
| RUN-003 | PSE-SEEN-ONLY-seed17-repeat1 | ablation | frozen | {"pse_apply_unseen":false} | 17 |  | V5ABL013-RUN-003 | 当前已见类使用 PSE 而未见类直接平均 |  |  |  |
| RUN-004 | PSE-SEEN-ONLY-seed17-repeat2 | ablation | frozen | {"pse_apply_unseen":false} | 17 | RUN-003 | V5ABL013-RUN-004 | 当前已见类使用 PSE 而未见类直接平均 |  |  |  |
| RUN-005 | PSE-SHARED-UNSEEN-seed5-repeat1 | ablation | frozen | {"pse_apply_unseen":true} | 5 |  | V5ABL013-RUN-005 | 评估时同一个 PSE 同时处理已见类和未见类 |  |  |  |
| RUN-006 | PSE-SHARED-UNSEEN-seed5-repeat2 | ablation | frozen | {"pse_apply_unseen":true} | 5 | RUN-005 | V5ABL013-RUN-006 | 评估时同一个 PSE 同时处理已见类和未见类 |  |  |  |
| RUN-007 | PSE-SHARED-UNSEEN-seed17-repeat1 | ablation | frozen | {"pse_apply_unseen":true} | 17 |  | V5ABL013-RUN-007 | 评估时同一个 PSE 同时处理已见类和未见类 |  |  |  |
| RUN-008 | PSE-SHARED-UNSEEN-seed17-repeat2 | ablation | frozen | {"pse_apply_unseen":true} | 17 | RUN-007 | V5ABL013-RUN-008 | 评估时同一个 PSE 同时处理已见类和未见类 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
