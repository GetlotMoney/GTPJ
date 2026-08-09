# 参数矩阵：CONFIRM-001_v5-code-equivalence

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：R2 新编号；R1 失败批次保存在 evidence/FORMAL_BATCH_R1.csv

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-006 | 今天模板等价配置R2复跑1 | confirmation | frozen | {} | 5 | matrix:experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/evidence/FORMAL_BATCH_R1.csv#RUN-001 | V5CONF001-R2-CURRENT-001 | 用老V5有效参数的瘦身投影验证今天代码 |  |  |  |
| RUN-007 | 今天模板等价配置R2复跑2 | confirmation | frozen | {} | 5 | matrix:experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/evidence/FORMAL_BATCH_R1.csv#RUN-002 | V5CONF001-R2-CURRENT-002 | 用老V5有效参数的瘦身投影验证今天代码 |  |  |  |
| RUN-008 | 今天模板等价配置R2复跑3 | confirmation | frozen | {} | 5 | matrix:experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/evidence/FORMAL_BATCH_R1.csv#RUN-003 | V5CONF001-R2-CURRENT-003 | 用老V5有效参数的瘦身投影验证今天代码 |  |  |  |
| RUN-009 | 今天模板等价配置R2复跑4 | confirmation | frozen | {} | 5 | matrix:experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/evidence/FORMAL_BATCH_R1.csv#RUN-004 | V5CONF001-R2-CURRENT-004 | 用老V5有效参数的瘦身投影验证今天代码 |  |  |  |
| RUN-010 | 今天模板等价配置R2复跑5 | confirmation | frozen | {} | 5 | matrix:experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/evidence/FORMAL_BATCH_R1.csv#RUN-005 | V5CONF001-R2-CURRENT-005 | 用老V5有效参数的瘦身投影验证今天代码 |  |  |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
