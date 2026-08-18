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
| `V5-INNOVATION-011` | planned | 删除旧频域、旧局部分支、拓扑和多辅助损失后，干净 V6 候选是否能证明句子—区域交互本身合理 | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/PARAMETER_MATRIX.md` | `IDEA-0013` | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate` | - |
| `V5-INNOVATION-012` | completed | 8 句纯 CLIP 全局零模块基线 H=64.164039；用于后续单模块比较，不作为原创贡献 | `experiments/v5/innovation/INNOVATION-012_global8_clip_baseline/PARAMETER_MATRIX.md` | - | `experiments/v5/innovation/INNOVATION-012_global8_clip_baseline` | - |
| `V5-INNOVATION-013` | completed | 共享 PSE 单模块 H=68.613253，较纯 CLIP 八句基线提高 +4.449214；单 seed 未确认 | `experiments/v5/innovation/INNOVATION-013_shared_pse_global8/PARAMETER_MATRIX.md` | - | `experiments/v5/innovation/INNOVATION-013_shared_pse_global8` | - |
| `V5-INNOVATION-014` | completed | official-test gamma score search 得到 H=70.585674；仅为路线容量诊断，不是 confirmation evidence | `experiments/v5/innovation/INNOVATION-014_pse_seen_bias_calibration/PARAMETER_MATRIX.md` | - | `experiments/v5/innovation/INNOVATION-014_pse_seen_bias_calibration` | - |
| `V5-INNOVATION-015` | rejected | TE-PSE 的 RUN-001 得到 H=63.70，比同次 B0 低 0.46；停止，不进入 seed 17 | `experiments/v5/innovation/INNOVATION-015_te_pse/PARAMETER_MATRIX.md` | `owner_conversation_2026_08_15` | `experiments/v5/innovation/INNOVATION-015_te_pse` | - |
| `V5-INNOVATION-016` | rejected | VSC 与父 TE-PSE 的 U/S/H/ZS 完全相同，H=63.70；无增益并停止 controls | `experiments/v5/innovation/INNOVATION-016_te_pse_vsc/PARAMETER_MATRIX.md` | `owner_conversation_2026_08_15` | `experiments/v5/innovation/INNOVATION-016_te_pse_vsc` | - |
| `V5-INNOVATION-017` | rejected | VCER H=64.12，比同次 X2 低 9.40；role-shuffle 反而更高，角色因果门失败并停止 | `experiments/v5/innovation/INNOVATION-017_vcer/PARAMETER_MATRIX.md` | `IDEA-0014` | `experiments/v5/innovation/INNOVATION-017_vcer` | - |
| `V5-INNOVATION-018` | completed | DPEF official-test 341 点 score search 得到 H=76.447016；只证明已披露测试集上限，not confirmation evidence | `experiments/v5/innovation/INNOVATION-018_dual_prototype_expert_fusion/PARAMETER_MATRIX.md` | `IDEA-0016` | `experiments/v5/innovation/INNOVATION-018_dual_prototype_expert_fusion` | - |
| `V5-INNOVATION-019` | rejected | RCDP H=66.336303，较同次 Mean8 低 0.306272；提高 S/ZS 但损失更多 U，停止 | `experiments/v5/innovation/INNOVATION-019_role_contrastive_displacement_prototype/PARAMETER_MATRIX.md` | `IDEA-0017` | `experiments/v5/innovation/INNOVATION-019_role_contrastive_displacement_prototype` | - |
| `V5-INNOVATION-020` | rejected | RACE H=66.541096，较 Mean8 低 0.101480；wrong-role 近似且 no-contrast 更高，机制不成立 | `experiments/v5/innovation/INNOVATION-020_role_aligned_competitive_evidence/PARAMETER_MATRIX.md` | `IDEA-0018` | `experiments/v5/innovation/INNOVATION-020_role_aligned_competitive_evidence` | - |
| `V5-INNOVATION-021` | rejected | FRPE H=66.974786，较 Mean8 仅 +0.332210；后续 GALA 对 U/S/H 净贡献为 0 且损害 ZS，均停止 | `experiments/v5/innovation/INNOVATION-021_faithful_role_patch_evidence/PARAMETER_MATRIX.md` | `IDEA-0019` | `experiments/v5/innovation/INNOVATION-021_faithful_role_patch_evidence` | - |
| `V5-INNOVATION-022` | rejected | ARTV 得到 H=70.05，比同次 X2 低 3.47；角色干预有弱信号但主路径净伤害，停止且不调阈值 | `experiments/v5/innovation/INNOVATION-022_artv/PARAMETER_MATRIX.md` | `IDEA-0015` | `experiments/v5/innovation/INNOVATION-022_artv` | - |
| `V5-INNOVATION-023` | rejected | RPR 历史主条件 H=51.838248；因旧 017 与 VCER 冲突，保留原 commit/artifact 并映射到 023 | `experiments/v5/innovation/INNOVATION-023_rpr_legacy_mapping/PARAMETER_MATRIX.md` | `IDEA-0020` | `experiments/v5/innovation/INNOVATION-023_rpr_legacy_mapping` | - |

## 编号与证据边界

- `V5-INNOVATION-017` 当前只代表 VCER。历史 RPR 分支曾复用 017，结果为 `U/S/H/ZS=45.918182/59.510756/51.838248/66.249114`、`stop_no_gain`；它通过 `V5-INNOVATION-023 / legacy_summary_only` 回查，不覆盖 VCER，也不改写历史配置、commit 或 artifact URI。
- `V5-INNOVATION-014` 与 `V5-INNOVATION-018` 都直接使用 official test 做 score search，分别只是 gamma 校准和双原型融合的 test-exposed 上限；不得当作无 test 调参的正式成绩。
- GALA 是 `V5-INNOVATION-021` 下的 `RUN-DEBUG-GALA`，不另占创新编号。它的 gate-on 与 gate-off U/S/H 相同，ZS 下降 `1.145333`，结论仍是停止。

## 本地创新筛选总账入口

尚未注册为独立 `V5-INNOVATION-xxx` 的本地创新也不能丢失或只记录成功项。完整 U/S/H/ZS、比较基线、代码或配置身份、证据 SHA 和停止原因，以 `experiments/v5/MODULES.md` 的“本地模块筛选清单”及后续日期章节为权威记录。当前已登记：

- 文本与原型基座：GPT-5.5 七句 RCE、八句 Mean8、八句 RCE、SharedPSE。
- 早期视觉/角色模块：TransZero patch margin、PSE+视觉联合训练、ICRP、CRTP、RCG、SPV、RSMR、CSRT、RTA-PSE seen-CE、RTA-PSE class-disjoint、RTA+文本区分度先验、RICA-v0、CRGT、DATA-PSE。
- 强 PSE 复原与替换：PSE-A、PSE-B、DCRA-PSE/PSE-C、PSE-X1、PSE-X2、RBD-PSE、BRVM-PSE、RC-GDT、validation-selected 双原型 PSE-D、未启动的 CF-Role。
- 角色视觉与迁移：CHORM-TIED、CHORM-ROLE、HSP-PSE V1、HSP-PSE V2、HSTB、HSTB-V2、CVEI、HSTB-V2+CVEI、REDM、被门控取消的 CLPF、CRPC。
- 局部分支瘦身：六部位 FRPE、PSE+ICSA、Topology Pearson loss、GALA hard-rival gate。

其中 RCG、RCG+CSRT 等仅保留本地正信号，HSTB 的 `Delta H=+0.373591` 也因 S 与机制门失败而停止；这些结果都没有完成正式晋级所需的干净验证，不能从本地筛选直接升级为新框架或论文结论。
