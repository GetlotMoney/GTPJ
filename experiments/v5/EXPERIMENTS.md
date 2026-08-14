# FRAMEWORK-V5 实验总览

> 本页由四个类型 INDEX 自动生成。请修改对应 INDEX 后运行 `python workflow/gtpj_workflow.py refresh-framework-view --version v5`，不要手工维护第二份结论。

| 类型 | 实验数 | 正式台账 |
|---|---:|---|
| 调参 | 4 | `tune/INDEX.md` |
| 消融 | 13 | `ablation/INDEX.md` |
| 创新 | 12 | `innovation/INDEX.md` |
| 确认 | 5 | `confirmation/INDEX.md` |

## 调参实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-TUNE-001` | completed | 动态方向路由的 hidden、权重、anchor 和模式怎样影响结果 | `experiments/v5/tune/TUNE-001_dynamic_routing_search/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-006/TUNE-001..008` | `experiments/v5/tune/TUNE-001_dynamic_routing_search` | - |
| `V5-TUNE-002` | pre_run_gated | 固定 V5 其余语义时，局部分支融合权重取多少更合适 | `experiments/v5/tune/TUNE-002_local_fusion_weight/PARAMETER_MATRIX.md` | `-` | `experiments/v5/tune/TUNE-002_local_fusion_weight` | - |
| `V5-TUNE-003` | pre_run_gated | FGVD 选择的局部块数量怎样影响结果 | `experiments/v5/tune/TUNE-003_fgvd_select_k/PARAMETER_MATRIX.md` | `-` | `experiments/v5/tune/TUNE-003_fgvd_select_k` | - |
| `V5-TUNE-004` | pre_run_gated | SGMP 的 top-k 设为 16 会怎样影响结果 | `experiments/v5/tune/TUNE-004_sgmp_topk/PARAMETER_MATRIX.md` | `-` | `experiments/v5/tune/TUNE-004_sgmp_topk` | - |

## 消融实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-ABLATION-001` | completed | 完整 V5 与彻底移除 FGVD/BVSA/SGMP 及局部损失后的性能差多少；三种子平均 H 差值 `+0.08`，strict-3 已通过 | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` | `codex/attempt019-local-ablation#ATTEMPT-019` | `experiments/v5/ablation/ABLATION-001_local_branch_effect` | - |
| `V5-ABLATION-002` | pre_run_gated | 关闭 PSE 后，完整 V5 的 U、S、H、ZS 是否出现稳定变化 | `experiments/v5/ablation/ABLATION-002_pse_effect/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-002_pse_effect` | - |
| `V5-ABLATION-003` | pre_run_gated | 关闭 ICSA 后，完整 V5 的 U、S、H、ZS 是否出现稳定变化 | `experiments/v5/ablation/ABLATION-003_icsa_effect/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-003_icsa_effect` | - |
| `V5-ABLATION-004` | completed | 只跳过 FGVD 几何编码时，最终 H 是否持平或提高 | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect/PARAMETER_MATRIX.md` | `exp/v5/ablation/ablation-004-fgvd-geometry-effect@ab51e36` | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect` | - |
| `V5-ABLATION-005` | pre_run_gated | SGMP 的 MPP 与 NEG 损失系数分别贡献多少 | `experiments/v5/ablation/ABLATION-005_sgmp_loss_effect/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-005_sgmp_loss_effect` | - |
| `V5-ABLATION-006` | pre_run_gated | 五项辅助损失及关键子项分别贡献多少 | `experiments/v5/ablation/ABLATION-006_auxiliary_loss_effect/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-006_auxiliary_loss_effect` | - |
| `V5-ABLATION-007` | pre_run_gated | Topology Pearson 损失贡献多少 | `experiments/v5/ablation/ABLATION-007_topology_loss_effect/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-007_topology_loss_effect` | - |
| `V5-ABLATION-008` | pre_run_gated | 冻结 CLIP、仅全局、仅局部与完整 V5 各自贡献多少 | `experiments/v5/ablation/ABLATION-008_clip_global_local_factorial/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-008_clip_global_local_factorial` | - |
| `V5-ABLATION-009` | pre_run_gated | BVSA 最终局部分数的方向权重怎样影响结果 | `experiments/v5/ablation/ABLATION-009_bvsa_direction_effect/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-009_bvsa_direction_effect` | - |
| `V5-ABLATION-010` | pre_run_gated | 同时关闭 PSE 与 ICSA 后，两个语义适配模块是互补还是重复 | `experiments/v5/ablation/ABLATION-010_pse_icsa_interaction/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-010_pse_icsa_interaction` | - |
| `V5-ABLATION-011` | completed | 只保留当前 V5 全局分数路径时，性能相对完整母版如何变化 | `experiments/v5/ablation/ABLATION-011_current_global_only/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-011_current_global_only` | - |
| `V5-ABLATION-012` | ready_to_run | PSE 的 Q/K 注意力是否真正有效，以及清零是否由权重衰减造成 | `experiments/v5/ablation/ABLATION-012_pse_attention_validation/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-012_pse_attention_validation` | - |
| `V5-ABLATION-013` | ready_to_run | 同一个 PSE 是否应该在评估时同时处理已见类和未见类文本 | `experiments/v5/ablation/ABLATION-013_pse_shared_unseen/PARAMETER_MATRIX.md` | `-` | `experiments/v5/ablation/ABLATION-013_pse_shared_unseen` | - |

## 创新实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-INNOVATION-001` | candidate | 动态残差路由是否值得成为新框架 | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-001..018` | `experiments/v5/innovation/INNOVATION-001_dynamic_routing` | - |
| `V5-INNOVATION-002` | rejected | 对齐全局与局部分数的温度尺度后，局部分支是否产生稳定且有意义的增益；Stage 1 三组 H 均下降，平均 ΔH=-3.03 | `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/PARAMETER_MATRIX.md` | `-` | `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion` | - |
| `V5-INNOVATION-003` | completed | 全局分支低置信度时按置信度增强局部分支，能否比固定融合提供更稳定的互补信息 | `experiments/v5/innovation/INNOVATION-003_confidence_local_gate/PARAMETER_MATRIX.md` | `IDEA-0005` | `experiments/v5/innovation/INNOVATION-003_confidence_local_gate` | - |
| `V5-INNOVATION-004` | completed | FGVD-off 后增加局部 CE 能否提高局部可靠性和最终 H | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd` | - |
| `V5-INNOVATION-005` | completed | 全局混淆难负类监督能否增加局部 rescue 并减少 harm | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast` | - |
| `V5-INNOVATION-006` | completed | 真实裁剪 CLS teacher 能否提高局部证据稳定性和最终 H | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation` | - |
| `V5-INNOVATION-007` | completed | 局部证据只在全局 top-5 内有界重排时能否增加 rescue 并控制 harm | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking` | - |
| `V5-INNOVATION-008` | rejected | 限幅、对称且保留句子 PSE 的类别关系增强未提高 H；R0/R1/R2 为 69.91/61.27/58.14，未进入正式测试 | `experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration/PARAMETER_MATRIX.md` | `-` | `experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration` | - |
| `V5-INNOVATION-009` | rejected | 只让全局图像选择8句话是否已经足够；RUN-002 H=59.41，未保留 | `experiments/v5/innovation/INNOVATION-009_image_conditioned_pse/PARAMETER_MATRIX.md` | `IDEA-0011` | `experiments/v5/innovation/INNOVATION-009_image_conditioned_pse` | - |
| `V5-INNOVATION-010` | rejected | 统一的 8 句—全局/Top-K32 区域双向匹配能否比实验 A 进一步提高 H；RUN-001 H=58.92，未保留 | `experiments/v5/innovation/INNOVATION-010_pse_vsce/PARAMETER_MATRIX.md` | `IDEA-0012` | `experiments/v5/innovation/INNOVATION-010_pse_vsce` | - |
| `V5-INNOVATION-011` | planned | 删除旧频域、旧局部分支、拓扑和多辅助损失后，干净 V6 候选是否能证明句子—区域交互本身合理 | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/PARAMETER_MATRIX.md` | `IDEA-0013` | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate` | - |
| `V5-INNOVATION-015` | ready_to_run | 无 self-attention 的同角色 hard-rival 加性证据能否提高 GPT-5.6 八句纯 CLIP 的 raw GZSL H | `experiments/v5/innovation/INNOVATION-015_te_pse/PARAMETER_MATRIX.md` | `owner_conversation_2026_08_15` | `experiments/v5/innovation/INNOVATION-015_te_pse` | - |

## 确认实验

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-CONFIRM-001` | pre_run | 老 V5 与今天模板同配置对跑，并诊断复跑动态路由 75.11 | `experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/PARAMETER_MATRIX.md` | `trial003-main100-069; ATTEMPT-017/DR-095` | `experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence` | - |
| `V5-CONFIRM-002` | planned | 不恢复无用层时，能否让干净 V5 的同 seed 初始化与老 V5 完全对齐并复现约 74.4 H | `experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence/PARAMETER_MATRIX.md` | `v5@4b259379d99c1a791442ea9e2fac0bb22b2411a9` | `experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence` | - |
| `V5-CONFIRM-003` | completed | 最新 V5 母版同 seed 三次运行的基线分布与局部分支互补性是什么 | `experiments/v5/confirmation/CONFIRM-003_current_local_diagnosis/PARAMETER_MATRIX.md` | `-` | `experiments/v5/confirmation/CONFIRM-003_current_local_diagnosis` | - |
| `V5-CONFIRM-004` | completed | 最新代码完整框架五次最高 H=74.1941，未恢复到约 74.4 | `experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework/PARAMETER_MATRIX.md` | `trial003-main100-091..095` | `experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework` | - |
| `V5-CONFIRM-005` | completed | 老框架五次最高 H=74.3230，仍未恢复到 74.40 | `experiments/v5/confirmation/CONFIRM-005_historical_v5_reproduction/PARAMETER_MATRIX.md` | `trial003-old-v5-source@4b259379` | `experiments/v5/confirmation/CONFIRM-005_historical_v5_reproduction` | - |
