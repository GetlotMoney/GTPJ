# 参数矩阵：INNOVATION-001_conditional_bvsa

这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。

来源：TRIAL-003 中可核实的来源配置与冻结复跑；不是完整 100-run 搜索重建。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | source config | innovation | legacy_summary_only | {"bvsa_text_mode":"conditional","local_weight":0.2,"pse_outer_ratio":0.65} | 5 |  | trial003-main100-069 | preserve historical evidence | 74.43 | legacy_owner_activated |  |
| RUN-002 | frozen repeat | innovation | legacy_summary_only | {"bvsa_text_mode":"conditional","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | trial003-main100-091 | preserve historical evidence | 74.49 | repeat_evidence |  |
| RUN-003 | frozen repeat | innovation | legacy_summary_only | {"bvsa_text_mode":"conditional","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | trial003-main100-092 | preserve historical evidence | 74.43 | repeat_evidence |  |
| RUN-004 | frozen repeat | innovation | legacy_summary_only | {"bvsa_text_mode":"conditional","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | trial003-main100-093 | preserve historical evidence | 74.35 | repeat_evidence |  |
| RUN-005 | frozen repeat | innovation | legacy_summary_only | {"bvsa_text_mode":"conditional","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | trial003-main100-094 | preserve historical evidence | 74.41 | repeat_evidence |  |
| RUN-006 | best observed repeat | innovation | legacy_summary_only | {"bvsa_text_mode":"conditional","local_weight":0.2,"pse_outer_ratio":0.65} | 5 | RUN-001 | trial003-main100-095 | preserve historical evidence | 74.54 | repeat_evidence |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
