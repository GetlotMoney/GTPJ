# ATTEMPT-010 Result

状态：`completed_with_skips`，作为 workflow smoke 闭环完成；不作为正式 20-job top4 confirmation。

## 运行边界

- 服务器路径：`lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260705-0001-confirm-dr020-051-041-047-sameseed5x-2gpu`
- 原计划：`DR-020 / DR-051 / DR-041 / DR-047` 各 seed=5 same-seed exact repeat 5 次，共 20 jobs。
- 用户中途要求：再完成 2 个实验后停止，用于测试 workflow 完整闭环。
- 最终状态：4 completed、16 skipped、0 failed、0 running、0 pending。

## 已完成结果

| Source | Job | Repeat | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|---:|
| DR-020 | DR-001 | 1 | 72.43 | 76.97 | 74.63 | 81.61 | 48 |
| DR-020 | DR-002 | 2 | 72.73 | 76.58 | 74.61 | 81.45 | 48 |
| DR-020 | DR-003 | 3 | 72.26 | 76.77 | 74.44 | 81.21 | 37 |
| DR-020 | DR-004 | 4 | 72.53 | 76.96 | 74.68 | 81.72 | 47 |

## Partial Summary

| Source | completed/planned | best H | mean H | min H | max H | range H | mean U | mean S | mean ZS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DR-020 | 4/5 | 74.68 | 74.59 | 74.44 | 74.68 | 0.24 | 72.49 | 76.82 | 81.50 |
| DR-051 | 0/5 | pending | pending | pending | pending | pending | pending | pending | pending |
| DR-041 | 0/5 | pending | pending | pending | pending | pending | pending | pending | pending |
| DR-047 | 0/5 | pending | pending | pending | pending | pending | pending | pending | pending |

## Decision

`promotion_decision: blocked`。本轮只证明 workflow 链路可闭环：named-thread gate、服务器启动、summary 采集、用户停止、结果登记和 evidence routing 都可走通。正式 ATTEMPT-010 需要重新跑完整 20 jobs，或另建一个明确的 partial-repeat attempt。
