# FRAMEWORK-V5 消融实验索引

| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |
|---|---|---|---|---|---|---|
| `V5-ABLATION-001` | completed | 完整 V5 与彻底移除 FGVD/BVSA/SGMP 及局部损失后的性能差多少；三种子平均 H 差值 `+0.08`，strict-3 已通过 | `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md` | `codex/attempt019-local-ablation#ATTEMPT-019` | `experiments/v5/ablation/ABLATION-001_local_branch_effect` | - |
| `V5-ABLATION-002` | pre_run_gated | 关闭 PSE 后，完整 V5 的 U、S、H、ZS 是否出现稳定变化 | `experiments/v5/ablation/ABLATION-002_pse_effect/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-002_pse_effect` | - |
| `V5-ABLATION-003` | pre_run_gated | 关闭 ICSA 后，完整 V5 的 U、S、H、ZS 是否出现稳定变化 | `experiments/v5/ablation/ABLATION-003_icsa_effect/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-003_icsa_effect` | - |
| `V5-ABLATION-004` | completed | 只跳过 FGVD 几何编码时，最终 H 是否持平或提高 | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect/PARAMETER_MATRIX.md` | `exp/v5/ablation/ablation-004-fgvd-geometry-effect@ab51e36` | `experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect` | - |
| `V5-ABLATION-005` | pre_run_gated | SGMP 的 MPP 与 NEG 损失系数分别贡献多少 | `experiments/v5/ablation/ABLATION-005_sgmp_loss_effect/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-005_sgmp_loss_effect` | - |
| `V5-ABLATION-006` | pre_run_gated | 五项辅助损失及关键子项分别贡献多少 | `experiments/v5/ablation/ABLATION-006_auxiliary_loss_effect/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-006_auxiliary_loss_effect` | - |
| `V5-ABLATION-007` | pre_run_gated | Topology Pearson 损失贡献多少 | `experiments/v5/ablation/ABLATION-007_topology_loss_effect/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-007_topology_loss_effect` | - |
| `V5-ABLATION-008` | pre_run_gated | 冻结 CLIP、仅全局、仅局部与完整 V5 各自贡献多少 | `experiments/v5/ablation/ABLATION-008_clip_global_local_factorial/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-008_clip_global_local_factorial` | - |
| `V5-ABLATION-009` | pre_run_gated | BVSA 最终局部分数的方向权重怎样影响结果 | `experiments/v5/ablation/ABLATION-009_bvsa_direction_effect/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-009_bvsa_direction_effect` | - |
| `V5-ABLATION-010` | pre_run_gated | 同时关闭 PSE 与 ICSA 后，两个语义适配模块是互补还是重复 | `experiments/v5/ablation/ABLATION-010_pse_icsa_interaction/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-010_pse_icsa_interaction` | - |
| `V5-ABLATION-011` | completed | 只保留当前 V5 全局分数路径时，性能相对完整母版如何变化 | `experiments/v5/ablation/ABLATION-011_current_global_only/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-011_current_global_only` | - |
| `V5-ABLATION-012` | ready_to_run | PSE 的 Q/K 注意力是否真正有效，以及清零是否由权重衰减造成 | `experiments/v5/ablation/ABLATION-012_pse_attention_validation/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-012_pse_attention_validation` | - |
| `V5-ABLATION-013` | ready_to_run | 同一个 PSE 是否应该在评估时同时处理已见类和未见类文本 | `experiments/v5/ablation/ABLATION-013_pse_shared_unseen/PARAMETER_MATRIX.md` | - | `experiments/v5/ablation/ABLATION-013_pse_shared_unseen` | - |
