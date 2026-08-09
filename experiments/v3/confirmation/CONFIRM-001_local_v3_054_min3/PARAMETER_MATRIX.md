# 参数矩阵：CONFIRM-001_local_v3_054_min3

这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。

来源：min3_summary.csv 的三次已验证复跑结果；未知字段保持空白。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | local-v3-054 confirmation repeat 1 | confirmation | legacy_summary_only | {"clip_a_self_outer_ratio":0.5,"local_weight":0.1,"pse_outer_ratio":0.5} | 5 |  | RUN-20260629-1722-rep01 | preserve historical evidence | 74.46 | confirmed_config |  |
| RUN-002 | local-v3-054 confirmation repeat 2 | confirmation | legacy_summary_only | {"clip_a_self_outer_ratio":0.5,"local_weight":0.1,"pse_outer_ratio":0.5} | 5 | RUN-001 | RUN-20260629-1722-rep02 | preserve historical evidence | 74.42 | confirmed_config |  |
| RUN-003 | local-v3-054 confirmation repeat 3 | confirmation | legacy_summary_only | {"clip_a_self_outer_ratio":0.5,"local_weight":0.1,"pse_outer_ratio":0.5} | 5 | RUN-001 | RUN-20260629-1722-rep03 | preserve historical evidence | 74.47 | confirmed_config |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
