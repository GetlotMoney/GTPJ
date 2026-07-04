# GTPJ 当前待办

这是当前执行窗口，只保留近期优先动作；完整创意库不放在这里。

- 当前关注：GTPJ-v5 active mainline 后的近期复现、调参、队列整理和证据收尾。
- 管理规则：只保留 3-7 条近期动作；完整创意库看 idea_tree/INDEX.md；具体实验动作写入 task/trial/attempt。
- 更新时间：2026-07-04

## 当前窗口

| 优先级 | 事项 | 类型 | 负责人 | 状态 | 阻塞 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | 每次正式 campaign 结束后执行 Warehouse checkpoint retention，只保留 Top-5 best model_best/best-model files 并记录 manifest。 | artifact_retention | Coordinator | open | - | docs/workflow/reference/artifact_policy.md |
| P1 | 继续 v5-based tuning 或 ablation，配置来源必须是 config/versions/v5.yaml。 | tune_or_ablation | Coordinator | open | 需要 owner 指定调参、消融或混合实验范围。 | experiments/v5/ |
| P1 | 下一轮调参后，用 repeat mean 判断 v5 是否超过 v4 confirmed_H=74.45。 | confirmation_planning | Coordinator | open | 需要先产生新的候选结果。 | experiments/v5/confirmation/ |

## 已完成摘要

| 事项 | 证据位置 |
| --- | --- |
| 初始化 GTPJ repository 和 workflow helper。 | docs/PROJECT_STRUCTURE.md |
| 建立 GTPJ-v1 第一版正式 baseline，CUB seed=5 H=73.93。 | experiments/v1/baseline/result.yaml |
| 记录 GTPJ-v2 owner-activated，best_observed_H=74.29，confirmed_H pending。 | experiments/v2/baseline/result.yaml |
| 记录 GTPJ-v3 owner-accepted stochastic，best_observed_H=74.27，confirmed_H pending。 | experiments/v3/baseline/result.yaml |
| 确认 local-v3-054 server min3：H=74.46 / 74.42 / 74.47。 | experiments/v4/baseline/result.yaml |
| 激活 TRIAL-003 best conditional-BVSA-text candidate 为 GTPJ-v5 active mainline。 | experiments/v5/VERSION.md |
