# FRAMEWORK-V5 实验总览

> 本页由四个类型 INDEX 自动生成。请修改对应 INDEX 后运行 `python workflow/gtpj_workflow.py refresh-framework-view --version v5`，不要手工维护第二份结论。

| 类型 | 实验数 | 正式台账 |
|---|---:|---|
| 调参 | 1 | `tune/INDEX.md` |
| 消融 | 2 | `ablation/INDEX.md` |
| 创新 | 1 | `innovation/INDEX.md` |
| 确认 | 0 | `confirmation/INDEX.md` |

## 调参实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-TUNE-001` | completed | 动态方向路由的 hidden、权重、anchor 和模式怎样影响结果 | `experiments/v5/tune/TUNE-001_dynamic_routing_search/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-006/TUNE-001..008` | `experiments/v5/tune/TUNE-001_dynamic_routing_search` | - |

## 消融实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-ABLATION-001` | planned | 局部分支以及局部权重对结果到底有多大作用 | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` | `codex/attempt019-local-ablation#ATTEMPT-019` | `experiments/v5/ablation/ABLATION-001_local_branch_effect` | - |
| `V5-ABLATION-003` | planned | 关闭 ICSA 后，完整 V5 的 U、S、H、ZS 是否出现稳定变化 | `experiments/v5/ablation/ABLATION-003_icsa_effect/PARAMETER_MATRIX.md` | `V5-ABLATION-001/RUN-007,RUN-013,RUN-014` | `experiments/v5/ablation/ABLATION-003_icsa_effect` | - |

## 创新实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-INNOVATION-001` | candidate | 动态残差路由是否值得成为新框架 | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-001..018` | `experiments/v5/innovation/INNOVATION-001_dynamic_routing` | - |

## 确认实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| - | none | 暂无 | - | - | - | - |
