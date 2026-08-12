# FRAMEWORK-V5 创新实验索引

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-INNOVATION-001` | candidate | 动态残差路由是否值得成为新框架 | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` | `IDEA-0003/TRIAL-001/ATTEMPT-001..018` | `experiments/v5/innovation/INNOVATION-001_dynamic_routing` | - |
| `V5-INNOVATION-002` | rejected | 对齐全局与局部分数的温度尺度后，局部分支是否产生稳定且有意义的增益；Stage 1 三组 H 均下降，平均 ΔH=-3.03 | `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/PARAMETER_MATRIX.md` | - | `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion` | - |
| `V5-INNOVATION-003` | completed | 全局分支低置信度时按置信度增强局部分支，能否比固定融合提供更稳定的互补信息 | `experiments/v5/innovation/INNOVATION-003_confidence_local_gate/PARAMETER_MATRIX.md` | `IDEA-0005` | `experiments/v5/innovation/INNOVATION-003_confidence_local_gate` | - |
| `V5-INNOVATION-004` | completed | FGVD-off 后增加局部 CE 能否提高局部可靠性和最终 H | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd` | - |
| `V5-INNOVATION-005` | completed | 全局混淆难负类监督能否增加局部 rescue 并减少 harm | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast` | - |
| `V5-INNOVATION-006` | completed | 真实裁剪 CLS teacher 能否提高局部证据稳定性和最终 H | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation` | - |
| `V5-INNOVATION-007` | completed | 局部证据只在全局 top-5 内有界重排时能否增加 rescue 并控制 harm | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking/PARAMETER_MATRIX.md` | `IDEA-0006` | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking` | - |
| `V5-INNOVATION-008` | rejected | 限幅、对称且保留句子 PSE 的类别关系增强未提高 H；R0/R1/R2 为 69.91/61.27/58.14，未进入正式测试 | `experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration/PARAMETER_MATRIX.md` | - | `experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration` | - |
| `V5-INNOVATION-009` | rejected | 只让全局图像选择8句话是否已经足够；RUN-002 H=59.41，未保留 | `experiments/v5/innovation/INNOVATION-009_image_conditioned_pse/PARAMETER_MATRIX.md` | `IDEA-0011` | `experiments/v5/innovation/INNOVATION-009_image_conditioned_pse` | - |
| `V5-INNOVATION-010` | rejected | 统一的 8 句—全局/Top-K32 区域双向匹配能否比实验 A 进一步提高 H；RUN-001 H=58.92，未保留 | `experiments/v5/innovation/INNOVATION-010_pse_vsce/PARAMETER_MATRIX.md` | `IDEA-0012` | `experiments/v5/innovation/INNOVATION-010_pse_vsce` | - |
| `V5-INNOVATION-011` | candidate | 干净 8 句直接匹配的 RUN-001 得到 H=61.16，高于 009/010 但低于 V5 74.44；继续修改，不晋级 V6 | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/PARAMETER_MATRIX.md` | `IDEA-0013` | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate` | - |
