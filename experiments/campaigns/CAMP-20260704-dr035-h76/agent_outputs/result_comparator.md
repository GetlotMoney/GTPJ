# Result Comparator Output

role: `result_comparator`
agent_instance_id: `019f2cc0-c597-70c0-bf91-026fa3572e8b`
display_name: `CAMP-20260704-dr035-h76 | Result Comparator`
system_nickname: `Volta`
decision: allow_comparison_block_promotion

比较边界：

| Reference | 定位 | 状态 | 用法 |
|---|---|---|---|
| ATTEMPT-004 / DR-035 | 单次最高水位 | H=75.02 | `best_observed_H`，只用于筛选和排序。 |
| ATTEMPT-007 / DR-035 exact repeat | 当前 DR-035 复现簇 | mean H=74.61，min=74.58，range=0.04 | 当前最重要的 confirmed_candidate 对照。 |
| v3/CONFIRM-001 local-v3-054 | confirmed reference | confirmed_H=74.47 | confirmed config/reference。 |
| GTPJ-v5 | active mainline | repeat mean=74.44，provisional | 运行基底，不是 stronger confirmed baseline。 |

100 个 existing-routing tune 结束后，top candidate 只按 `best_observed_H / tune_promising` 记录。若单次超过 74.61 或 75.02，下一步是独立 min3；不能凭单次高分直接 promotion。纯调参即使复现通过，也只能成为父版本下 confirmed config/reference，不能自动开新 `vX`。
