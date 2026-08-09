# 动态路由旧 Attempt 映射

这不是参数矩阵。这里一行代表一个旧批次，用来回答“这个 Attempt 大致做了什么、跑了多少、证据在哪”；它绝不冒充一个真实 `RUN`。

| 旧批次 | 已知任务数 | 批次最高 H | 当前结论 | 恢复程度 | 正式去向 / 证据 |
|---|---:|---:|---|---|---|
| ATTEMPT-001 | 50 completed | 74.40 | rejected | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-002 | 50 + 44 completed | 70.84 | rejected | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-003 | 50 completed | 74.86 | tune_promising | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-004 | 50 completed | 75.02 | tune_promising / blocked | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-005 | 3 个已列复跑结果 | 74.39 | stopped_repeat_unstable | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-006 | 10 completed | 74.75 | tune_promising / blocked | 已恢复 2 个创新探针和 8 个调参任务 | `V5-INNOVATION-001`、`V5-TUNE-001`、旧 `WORK_ITEMS.md` |
| ATTEMPT-007 | 3 completed | 74.62 | confirmed_candidate / blocked | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-008 | 6 completed | 74.76 | not_confirmed / blocked | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-009 | 未知 | - | 根台账缺失 | 无法恢复 | 只保留编号空洞，不猜补 |
| ATTEMPT-010 | 4 completed | 74.68 | workflow smoke | 仅批次摘要 | 旧 `result.yaml` |
| ATTEMPT-011 | 200 组计划摘要 | 75.00 | follow_up_required / blocked | 只有分组数量 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-012 | 50 planned，部分完成 | 74.49 | stopped_by_owner | 只有候选×种子分组 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-013 | 50 planned，部分完成 | 74.53 | invalid confirmation scope | 只有分组参数 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-014 | 最多 100 planned | 74.99 | blocked | 只有恢复实验汇总 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-015 | 100 planned | 75.04 | tune_promising / blocked | 只有三组数量 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-016 | 10 planned | 74.85 | not_restored / blocked | 只有两候选×5 次 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-017 | 100 jobs | 75.11 | valid_single_run / blocked | 只有 7 类分组数量，没有逐任务配置 | 旧 `WORK_ITEMS.md`、`result.yaml` |
| ATTEMPT-018 | 5 次精确复跑 | 74.71 | not_restored / blocked | 结果可查，完整逐任务配置未在本仓库恢复 | 旧 `result.yaml` |

旧证据根目录：`experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/`。
