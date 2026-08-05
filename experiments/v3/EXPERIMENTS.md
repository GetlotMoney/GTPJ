# FRAMEWORK-V3 实验总览

> 本页由四个类型 INDEX 自动生成。请修改对应 INDEX 后运行 `python workflow/gtpj_workflow.py refresh-framework-view --version v3`，不要手工维护第二份结论。

| 类型 | 实验数 | 正式台账 |
|---|---:|---|
| 调参 | 1 | `tune/INDEX.md` |
| 消融 | 0 | `ablation/INDEX.md` |
| 创新 | 1 | `innovation/INDEX.md` |
| 确认 | 1 | `confirmation/INDEX.md` |

## 调参实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Child framework |
|---|---|---|---|---|---|---|
| `V3-TUNE-001` | completed | local-v3-054 参数组合是否稳定 | `experiments/v3/tune/TUNE-001_local_v3_054/PARAMETER_MATRIX.md` | `v4 historical config-only tag` | `experiments/v3/tune/TUNE-001_local_v3_054` | - |

## 消融实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Child framework |
|---|---|---|---|---|---|---|
| - | none | 暂无 | - | - | - | - |

## 创新实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Child framework |
|---|---|---|---|---|---|---|
| `V3-INNOVATION-001` | legacy_owner_activated | 条件 BVSA 文本路由能否形成新的主线框架 | `experiments/v3/innovation/INNOVATION-001_conditional_bvsa/PARAMETER_MATRIX.md` | `IDEA-0002/TRIAL-003/RUN-20260630-0002` | `experiments/v3/innovation/INNOVATION-001_conditional_bvsa` | FRAMEWORK-V5 |

## 确认实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Child framework |
|---|---|---|---|---|---|---|
| `V3-CONFIRM-001` | completed | local-v3-054 是否通过三次固定配置复跑 | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3/PARAMETER_MATRIX.md` | `RUN-20260629-1722` | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3` | - |
