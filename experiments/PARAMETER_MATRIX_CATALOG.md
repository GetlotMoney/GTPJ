# 参数矩阵总看板

每一行 `RUN-xxx` 都代表一次实际训练、一次计划运行，或一条明确记录的历史状态；结果、配置快照和外部证据位置均从同一张参数表回查。

原始日志、checkpoint、缓存和数据集不进 GitHub；GitHub 只保存轻量账本、配置快照、哈希和 Warehouse 位置。

| 实验 | RUN 行数 | 当前状态 | 阅读入口 |
|---|---:|---|---|
| `V1-INNOVATION-001` | 1 | 历史摘要 | `experiments/v1/innovation/INNOVATION-001_clip_a_self/PARAMETER_MATRIX.md` |
| `V1-CONFIRM-001` | 1 | completed | `experiments/v1/confirmation/CONFIRM-001_v1_seed5/PARAMETER_MATRIX.md` |
| `V2-INNOVATION-001` | 1 | 历史摘要 | `experiments/v2/innovation/INNOVATION-001_strict_conditional_jepa/PARAMETER_MATRIX.md` |
| `V3-TUNE-001` | 1 | 历史候选摘要 | `experiments/v3/tune/TUNE-001_local_v3_054/PARAMETER_MATRIX.md` |
| `V3-CONFIRM-001` | 3 | completed | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3/PARAMETER_MATRIX.md` |
| `V3-INNOVATION-001` | 6 | 历史来源与复跑 | `experiments/v3/innovation/INNOVATION-001_conditional_bvsa/PARAMETER_MATRIX.md` |
| `V5-TUNE-001` | 8 | completed | `experiments/v5/tune/TUNE-001_dynamic_routing_search/PARAMETER_MATRIX.md` |
| `V5-TUNE-002` | 16 | pre_run_gated | `experiments/v5/tune/TUNE-002_local_fusion_weight/PARAMETER_MATRIX.md` |
| `V5-TUNE-003` | 8 | pre_run_gated | `experiments/v5/tune/TUNE-003_fgvd_select_k/PARAMETER_MATRIX.md` |
| `V5-TUNE-004` | 4 | pre_run_gated | `experiments/v5/tune/TUNE-004_sgmp_topk/PARAMETER_MATRIX.md` |
| `V5-ABLATION-001` | 16 | completed | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-002` | 4 | pre_run_gated | `experiments/v5/ablation/ABLATION-002_pse_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-003` | 4 | pre_run_gated | `experiments/v5/ablation/ABLATION-003_icsa_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-004` | 1 | completed | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-005` | 12 | pre_run_gated | `experiments/v5/ablation/ABLATION-005_sgmp_loss_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-006` | 16 | pre_run_gated | `experiments/v5/ablation/ABLATION-006_auxiliary_loss_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-007` | 4 | pre_run_gated | `experiments/v5/ablation/ABLATION-007_topology_loss_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-008` | 16 | pre_run_gated | `experiments/v5/ablation/ABLATION-008_clip_global_local_factorial/PARAMETER_MATRIX.md` |
| `V5-ABLATION-009` | 8 | pre_run_gated | `experiments/v5/ablation/ABLATION-009_bvsa_direction_effect/PARAMETER_MATRIX.md` |
| `V5-ABLATION-010` | 4 | pre_run_gated | `experiments/v5/ablation/ABLATION-010_pse_icsa_interaction/PARAMETER_MATRIX.md` |
| `V5-ABLATION-011` | 3 | completed | `experiments/v5/ablation/ABLATION-011_current_global_only/PARAMETER_MATRIX.md` |
| `V5-ABLATION-012` | 8 | ready_to_run | `experiments/v5/ablation/ABLATION-012_pse_attention_validation/PARAMETER_MATRIX.md` |
| `V5-ABLATION-013` | 8 | ready_to_run | `experiments/v5/ablation/ABLATION-013_pse_shared_unseen/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-001` | 2 | candidate | `experiments/v5/innovation/INNOVATION-001_dynamic_routing/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-002` | 10 | rejected | `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-003` | 3 | completed | `experiments/v5/innovation/INNOVATION-003_confidence_local_gate/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-004` | 1 | completed | `experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-005` | 4 | completed | `experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-006` | 1 | completed | `experiments/v5/innovation/INNOVATION-006_crop_self_distillation/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-007` | 3 | completed | `experiments/v5/innovation/INNOVATION-007_topk_local_reranking/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-008` | 10 | rejected | `experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-009` | 2 | rejected | `experiments/v5/innovation/INNOVATION-009_image_conditioned_pse/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-010` | 1 | rejected | `experiments/v5/innovation/INNOVATION-010_pse_vsce/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-011` | 1 | planned | `experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-015` | 1 | frozen_not_launched | `experiments/v5/innovation/INNOVATION-015_te_pse/PARAMETER_MATRIX.md` |
| `V5-INNOVATION-016` | 1 | frozen_not_launched | `experiments/v5/innovation/INNOVATION-016_te_pse_vsc/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-001` | 5 | pre_run | `experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-002` | 5 | planned | `experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-003` | 3 | completed | `experiments/v5/confirmation/CONFIRM-003_current_local_diagnosis/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-004` | 5 | completed | `experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework/PARAMETER_MATRIX.md` |
| `V5-CONFIRM-005` | 5 | completed | `experiments/v5/confirmation/CONFIRM-005_historical_v5_reproduction/PARAMETER_MATRIX.md` |

## 历史迁移队列

历史 Trial/Attempt 已经逐步映射到正式框架实验。以后只有找到逐 RUN 配置、结果和证据位置时，才继续补充参数表；不能恢复的旧批次保持摘要状态，不猜参数。
