# 参数矩阵：TUNE-001_local_v3_054

这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。

来源：v3 CONFIRM-001 和历史 v4 配置标签；仅登记已知最终候选，不补猜搜索过程。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | local-v3-054 selected config | tune | legacy_summary_only | {"clip_a_self_outer_ratio":0.5,"local_weight":0.1,"pse_outer_ratio":0.5} | 5 |  | local-v3-054 | preserve historical evidence | 74.47 | selected_for_confirmation |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
