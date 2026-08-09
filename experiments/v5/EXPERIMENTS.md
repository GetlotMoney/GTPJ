# FRAMEWORK-V5 实验总览

> 本页由四个类型 INDEX 自动生成。请修改对应 INDEX 后运行 `python workflow/gtpj_workflow.py refresh-framework-view --version v5`，不要手工维护第二份结论。

| 类型 | 实验数 | 正式台账 |
|---|---:|---|
| 调参 | 1 | `tune/INDEX.md` |
| 消融 | 2 | `ablation/INDEX.md` |
| 创新 | 5 | `innovation/INDEX.md` |
| 确认 | 1 | `confirmation/INDEX.md` |

## 调参实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-TUNE-001` | completed | 动态方向路由的 hidden、权重、anchor 和模式怎样影响结果 | `experiments/v5/tune/TUNE-001_dynamic_routing_search/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-006/TUNE-001..008` | `experiments/v5/tune/TUNE-001_dynamic_routing_search` | - |

## 消融实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-ABLATION-001` | planned | 局部分支以及局部权重对结果到底有多大作用 | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` | `codex/attempt019-local-ablation#ATTEMPT-019` | `experiments/v5/ablation/ABLATION-001_local_branch_effect` | - |
| `V5-ABLATION-004` | completed | 只跳过 FGVD 几何编码时，最终 H 是否持平或提高 | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect/PARAMETER_MATRIX.md` | `exp/v5/ablation/ablation-004-fgvd-geometry-effect@ab51e36` | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect` | - |

## 创新实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-INNOVATION-001` | candidate | 动态残差路由是否值得成为新框架 | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-001..018` | `experiments/v5/innovation/INNOVATION-001_dynamic_routing` | - |
| `V5-INNOVATION-004` | completed | FGVD-off 后增加局部 CE 能否提高局部可靠性和最终 H | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd` | - |
| `V5-INNOVATION-005` | completed | 全局混淆难负类监督能否增加局部 rescue 并减少 harm | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast` | - |
| `V5-INNOVATION-006` | completed | 真实裁剪 CLS teacher 能否提高局部证据稳定性和最终 H | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation` | - |
| `V5-INNOVATION-007` | completed | 局部证据只在全局 top-5 内有界重排时能否增加 rescue 并控制 harm | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking` | - |

## 确认实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-CONFIRM-004` | completed | 最新代码完整框架五次最高 H=74.1941，未恢复到约 74.4 | `experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework/PARAMETER_MATRIX.md` | `trial003-main100-091..095` | `experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework` | - |
