# FRAMEWORK-V5 实验总览

本次干净发布只登记已经完成并审核过的局部分支消融。调参、创新和确认实验将在各自独立分支、独立账本完成后再加入，不从旧实验目录直接继承代码。

| 类型 | 已发布实验数 | 当前入口 |
|---|---:|---|
| 调参 `tune` | 0 | 暂无 |
| 消融 `ablation` | 1 | `ablation/INDEX.md` |
| 创新 `innovation` | 0 | 暂无 |
| 确认 `confirmation` | 0 | 暂无 |

## 已发布消融

| Experiment ID | 问题 | 结论 | 参数表 |
|---|---|---|---|
| `V5-ABLATION-001` | 整套局部分支是否稳定提高 H？ | 三种子平均 H 仅 `+0.08`，不能声称稳定增益 | `ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` |
