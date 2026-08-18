# 正式实验总表

这个文件只做全仓入口，具体参数、结果和证据以各实验目录为准。旧 `TRIAL / ATTEMPT` 只用于回查，不再作为新实验入口。

参数表总入口：`experiments/PARAMETER_MATRIX_CATALOG.md`。

## 正式框架

| 框架 | Tag | 状态 | 历史来源 |
|---|---|---|---|
| `FRAMEWORK-V1` | `v1` | 历史正式框架 | 初始框架 |
| `FRAMEWORK-V2` | `v2` | 历史正式框架 | `FRAMEWORK-V1` |
| `FRAMEWORK-V3` | `v3` | 历史正式框架 | `FRAMEWORK-V2` |
| `FRAMEWORK-V5` | `v5` | 当前研究框架 | `FRAMEWORK-V3` |

`v4` 是历史 config-only Tag，不占用正式框架编号。

## 正式实验账本

| 实验 | 框架 | 类型 | 状态 | 入口 |
|---|---|---|---|---|
| `V1-INNOVATION-001` | `FRAMEWORK-V1` | innovation | legacy_owner_accepted_unconfirmed | `experiments/v1/innovation/INNOVATION-001_clip_a_self/PARAMETER_MATRIX.md` |
| `V1-CONFIRM-001` | `FRAMEWORK-V1` | confirmation | completed | `experiments/v1/confirmation/CONFIRM-001_v1_seed5/result.md` |
| `V2-INNOVATION-001` | `FRAMEWORK-V2` | innovation | legacy_owner_accepted_unconfirmed | `experiments/v2/innovation/INNOVATION-001_strict_conditional_jepa/PARAMETER_MATRIX.md` |
| `V3-TUNE-001` | `FRAMEWORK-V3` | tune | completed | `experiments/v3/tune/TUNE-001_local_v3_054/PARAMETER_MATRIX.md` |
| `V3-CONFIRM-001` | `FRAMEWORK-V3` | confirmation | completed | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3/result.md` |
| `V3-INNOVATION-001` | `FRAMEWORK-V3` | innovation | legacy_owner_activated | `experiments/v3/innovation/INNOVATION-001_conditional_bvsa/PARAMETER_MATRIX.md` |
| `V5-TUNE-001` | `FRAMEWORK-V5` | tune | completed | `experiments/v5/tune/TUNE-001_dynamic_routing_search/result.md` |
| `V5-TUNE-002` | `FRAMEWORK-V5` | tune | pre_run_gated | `experiments/v5/tune/TUNE-002_local_fusion_weight/PARAMETER_MATRIX.md` |
| `V5-TUNE-003` | `FRAMEWORK-V5` | tune | pre_run_gated | `experiments/v5/tune/TUNE-003_fgvd_select_k/PARAMETER_MATRIX.md` |
| `V5-TUNE-004` | `FRAMEWORK-V5` | tune | pre_run_gated | `experiments/v5/tune/TUNE-004_sgmp_topk/PARAMETER_MATRIX.md` |
| `V5-ABLATION-001` | `FRAMEWORK-V5` | ablation | completed | `experiments/v5/ablation/ABLATION-001_local_branch_effect/result.md` |
| `V5-ABLATION-002` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-002_pse_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-003` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-003_icsa_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-004` | `FRAMEWORK-V5` | ablation | completed | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect/result.md` |
| `V5-ABLATION-005` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-005_sgmp_loss_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-006` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-006_auxiliary_loss_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-007` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-007_topology_loss_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-008` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-008_clip_global_local_factorial/PARAMETER_MATRIX.md` |
| `V5-ABLATION-009` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-009_bvsa_direction_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-010` | `FRAMEWORK-V5` | ablation | pre_run_gated | `experiments/v5/ablation/ABLATION-010_pse_icsa_interaction/PARAMETER_MATRIX.md` |
| `V5-ABLATION-011` | `FRAMEWORK-V5` | ablation | completed | `experiments/v5/ablation/ABLATION-011_current_global_only/result.md` |
| `V5-ABLATION-012` | `FRAMEWORK-V5` | ablation | ready_to_run | `experiments/v5/ablation/ABLATION-012_pse_attention_validation/PARAMETER_MATRIX.md` |
| `V5-ABLATION-013` | `FRAMEWORK-V5` | ablation | ready_to_run | `experiments/v5/ablation/ABLATION-013_pse_shared_unseen/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-001` | `FRAMEWORK-V5` | innovation | candidate | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-002` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/result.md` |
| `V5-INNOVATION-003` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-003_confidence_local_gate/result.md` |
| `V5-INNOVATION-004` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd/result.md` |
| `V5-INNOVATION-005` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast/result.md` |
| `V5-INNOVATION-006` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation/result.md` |
| `V5-INNOVATION-007` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking/result.md` |
| `V5-INNOVATION-008` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration/result.md` |
| `V5-INNOVATION-009` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-009_image_conditioned_pse/result.md` |
| `V5-INNOVATION-010` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-010_pse_vsce/result.md` |
| `V5-INNOVATION-011` | `FRAMEWORK-V5` | innovation | planned | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-012` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-012_global8_clip_baseline/result.md` |
| `V5-INNOVATION-013` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-013_shared_pse_global8/result.md` |
| `V5-INNOVATION-014` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-014_pse_seen_bias_calibration/result.md` |
| `V5-INNOVATION-015` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-015_te_pse/result.md` |
| `V5-INNOVATION-016` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-016_te_pse_vsc/result.md` |
| `V5-INNOVATION-017` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-017_vcer/result.md` |
| `V5-INNOVATION-018` | `FRAMEWORK-V5` | innovation | completed | `experiments/v5/innovation/INNOVATION-018_dual_prototype_expert_fusion/result.md` |
| `V5-INNOVATION-019` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-019_role_contrastive_displacement_prototype/result.md` |
| `V5-INNOVATION-020` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-020_role_aligned_competitive_evidence/result.md` |
| `V5-INNOVATION-021` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-021_faithful_role_patch_evidence/result.md` |
| `V5-INNOVATION-022` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-022_artv/result.md` |
| `V5-INNOVATION-023` | `FRAMEWORK-V5` | innovation | rejected | `experiments/v5/innovation/INNOVATION-023_rpr_legacy_mapping/result.md` |
| `V5-CONFIRM-001` | `FRAMEWORK-V5` | confirmation | pre_run | `experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-002` | `FRAMEWORK-V5` | confirmation | planned | `experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-003` | `FRAMEWORK-V5` | confirmation | completed | `experiments/v5/confirmation/CONFIRM-003_current_local_diagnosis/result.md` |
| `V5-CONFIRM-004` | `FRAMEWORK-V5` | confirmation | completed | `experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework/result.md` |
| `V5-CONFIRM-005` | `FRAMEWORK-V5` | confirmation | completed | `experiments/v5/confirmation/CONFIRM-005_historical_v5_reproduction/result.md` |

## 历史 Trial 回查

| Trial | Idea | 状态 | 目录 | 说明 |
|---|---|---|---|---|
| `TRIAL-001_clip_a_self_residual_seenonly` | `IDEA-0001` | owner_activated_to_v2 | `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly` | 历史结果用于回查，已映射到 V1/V2 记录。 |
| `TRIAL-002_strict_conditional_jepa` | `IDEA-0002` | owner_accepted_to_v3 | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa` | 历史结果用于回查，已映射到 V2/V3 记录。 |
| `TRIAL-003_conditional_bvsa_text` | `IDEA-0002` | owner_activated_to_v5 | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text` | 历史结果用于回查，已映射到 V5 记录。 |
