# 参数矩阵：CONFIRM-001_v1_seed5

这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。

来源：旧 manifest/result 的已验证结果摘要；缺失字段保持空白。

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-001 | v1 seed5 confirmation | confirmation | legacy_summary_only | {} | 5 |  | attempt-001 | preserve historical evidence | 73.77 | keep |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
