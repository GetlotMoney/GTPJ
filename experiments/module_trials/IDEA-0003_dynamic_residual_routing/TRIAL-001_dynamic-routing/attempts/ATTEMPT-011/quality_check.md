# ATTEMPT-011 Quality Check

## 当前结论

ATTEMPT-011 服务器 detached campaign 已收口：200 completed / 0 failed / 0 skipped。结果可作为 ATTEMPT-014 候选来源，但不能作为 confirmed baseline 或 promotion 证据。

## 已检查

- 4 个 batch 均存在服务器 `summary.csv/jsonl`、`batch_status.json`、`events.jsonl` 和 `plan.json`。
- 服务器 summary 合计 200 行，completed=200。
- 最高单次 H=75.00，出现两条：`b01 DR-042` 和 `b04 DR-036`。
- top4 same-seed repeat 均已统计 best / mean / min / max / range。
- `direction_sample h48` 小 anchor 区域继续是主要热点。
- promotion 仍 blocked。

## 质量边界

- ATTEMPT-011 是 mixed search/repeat/ablation campaign，不是单一 confirmation。
- 历史 repeat 每候选 10 次，超过当前新规则的 max5；它只保留为历史事实，不作为新工作流模板。
- ATTEMPT-014 必须使用新的 exact-repeat 规则：原 seed、原配置、每候选最多 5 次、命中 `restore_target_H` 才算还原。
- `near_miss_not_restored` 只能说明有效果和希望，不能写成 confirmation。

## 未完成

- 尚未启动 ATTEMPT-014。
- 尚未为 ATTEMPT-014 生成服务器端运行事实。
- 尚未获得稳定 75+ repeat/promotion 证据。
