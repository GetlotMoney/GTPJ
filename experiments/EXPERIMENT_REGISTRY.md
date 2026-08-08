# Experiment Registry

Project: GTPJ

参数表总入口：`experiments/PARAMETER_MATRIX_CATALOG.md`。从 2026-08-04 起，每个新实验必须在自己的目录中保存逐任务 `PARAMETER_MATRIX.csv` 与阅读版 `PARAMETER_MATRIX.md`；本文件仍只管理版本和实验的总索引。

## Versions

| Version | Status | Code tag | Config | Note |
|---|---|---|---|---|
| `GTPJ-v1` | confirmed | `v1` | `experiments/v1/config.yaml` | First formal baseline, CUB seed=5 H=73.93. |
| `GTPJ-v2` | owner_activated_unconfirmed | `v2` | `experiments/v2/config.yaml` | CLIP-A-self text prototype adapter, best_observed_H=74.29, confirmed_H=pending, based on TRIAL-001 / ATTEMPT-019. |
| `GTPJ-v3` | owner_accepted_stochastic_unconfirmed | `v3` | `experiments/v3/config.yaml` | Strict conditional FAE-memory JEPA, best_observed_H=74.27, confirmed_H=pending, based on TRIAL-002 / ATTEMPT-004. |
| `GTPJ-v4` | legacy_config_only | `v4` | `experiments/v4/config.yaml` | Historical config-only tag for `v3/CONFIRM-001 local-v3-054`; not a formal framework version. |
| `GTPJ-v5` | owner_activated_provisional | `v5` | `experiments/v5/config.yaml` | TRIAL-003 conditional BVSA text active mainline from `trial003-main100-069`; best_observed_H=74.54, confirmed_H=74.44; strongest confirmed reference is `v3/CONFIRM-001 local-v3-054`. |

## 正式框架实验

| Experiment ID | Framework | Type | Status | Directory | Legacy / Child |
|---|---|---|---|---|---|
| `V1-INNOVATION-001` | `FRAMEWORK-V1` | innovation | legacy_owner_accepted_unconfirmed | `experiments/v1/innovation/INNOVATION-001_clip_a_self` | `IDEA-0001/TRIAL-001/ATTEMPT-019 -> FRAMEWORK-V2；历史接纳，未按新规确认` |
| `V1-CONFIRM-001` | `FRAMEWORK-V1` | confirmation | completed | `experiments/v1/confirmation/CONFIRM-001_v1_seed5` | `attempt-001` |
| `V2-INNOVATION-001` | `FRAMEWORK-V2` | innovation | legacy_owner_accepted_unconfirmed | `experiments/v2/innovation/INNOVATION-001_strict_conditional_jepa` | `IDEA-0002/TRIAL-002/ATTEMPT-004 -> FRAMEWORK-V3；历史接纳，未按新规确认` |
| `V3-TUNE-001` | `FRAMEWORK-V3` | tune | completed | `experiments/v3/tune/TUNE-001_local_v3_054` | `v4 legacy config-only` |
| `V3-CONFIRM-001` | `FRAMEWORK-V3` | confirmation | completed | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3` | `RUN-20260629-1722` |
| `V3-INNOVATION-001` | `FRAMEWORK-V3` | innovation | legacy_owner_activated | `experiments/v3/innovation/INNOVATION-001_conditional_bvsa` | `TRIAL-003 -> FRAMEWORK-V5；历史 owner 激活` |
| `V5-ABLATION-001` | `FRAMEWORK-V5` | ablation | planned | `experiments/v5/ablation/ABLATION-001_local_branch_effect` | `ATTEMPT-019 / DR-001..015` |
| `V5-TUNE-001` | `FRAMEWORK-V5` | tune | completed | `experiments/v5/tune/TUNE-001_dynamic_routing_search` | `ATTEMPT-006 / DR-003..010，8 个真实任务` |
| `V5-INNOVATION-001` | `FRAMEWORK-V5` | innovation | candidate | `experiments/v5/innovation/INNOVATION-001_dynamic_routing` | `ATTEMPT-006 / DR-001..002 已逐任务恢复；其余见 LEGACY_ATTEMPT_MAP.md` |

以下 Module Trials 表仅为旧编号回查，不再是人类主入口。

## Module Trials

| Trial | Idea | Status | Directory | Note |
|---|---|---|---|---|
| `TRIAL-001_clip_a_self_residual_seenonly` | `IDEA-0001` | owner_activated_to_v2 | `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly` | ATTEMPT-019 best_observed_H=74.29 is owner-activated as `GTPJ-v2`; clean confirmation and U/S gap review remain follow-ups. |
| `TRIAL-002_strict_conditional_jepa` | `IDEA-0002` | owner_accepted_to_v3 | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa` | ATTEMPT-004 best_observed_H=74.27 is owner-accepted as `GTPJ-v3`; seed-42 reruns show stochastic variance, so confirmed_H remains pending. |
| `TRIAL-003_conditional_bvsa_text` | `IDEA-0002` | owner_activated_to_v5 | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text` | `all_text_cond` enters BVSA cross/local_score; main100 best repeat H=74.54 and frozen-repeat mean H=74.44; owner activated as `GTPJ-v5`. |

## Version Experiments

| Experiment | Version | Type | Status | Directory | Note |
|---|---|---|---|---|---|
| `CONFIRM-001_v1_seed5` | `v1` | `confirmation` | keep | `experiments/v1/confirmation/CONFIRM-001_v1_seed5` | H=73.77, delta_H=-0.16; Warehouse artifacts registered. |
| `CONFIRM-001_local_v3_054_min3` | `v3` | `confirmation` | confirmed_config | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3` | Server min3 H=74.46/74.42/74.47, confirmed_H=74.47, H_mean=74.45; confirmed config under v3. Historical `v4` tag is config-only, not a formal framework version. |
| `V5-ABLATION-002` | `v5` | `ablation` | pre_run_gated | `experiments/v5/ablation/ABLATION-002_pse_effect` | 关闭 PSE；三个 seed 与 V5-ABLATION-001 的完整 V5 对照逐一配对。 |
