# 参数矩阵：INNOVATION-001_strict_conditional_jepa

这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。

来源：IDEA-0002 / TRIAL-002 / ATTEMPT-004 的历史结果摘要；原记录为 needs_confirmation / blocked，后续是 owner 历史接纳，不是新规确认晋级。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | strict conditional JEPA summary | innovation | legacy_summary_only | {"jepa_context_mode":"fae_main_memory","jepa_text_mode":"conditional"} | 5 |  | ATTEMPT-004 | preserve historical evidence | 74.27 | legacy_owner_accepted_unconfirmed |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
