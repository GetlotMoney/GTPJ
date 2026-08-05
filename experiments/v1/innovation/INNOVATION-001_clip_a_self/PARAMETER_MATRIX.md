# 参数矩阵：INNOVATION-001_clip_a_self

这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。

来源：IDEA-0001 / TRIAL-001 / ATTEMPT-019 的历史结果摘要；原 promotion_decision 为 blocked，后续是 owner 历史接纳，不是新规确认晋级。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | CLIP-A-self innovation summary | innovation | legacy_summary_only | {"apply_unseen":false,"inner_ratio":0.35,"outer_ratio":0.15,"use_clip_a_self":true} | 5 |  | ATTEMPT-019 | preserve historical evidence | 74.29 | legacy_owner_accepted_unconfirmed |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
