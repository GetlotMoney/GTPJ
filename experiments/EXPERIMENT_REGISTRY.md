# Experiment Registry

Project: GTPJ

## Versions

| Version | Status | Code tag | Config | Note |
|---|---|---|---|---|
| `GTPJ-v1` | confirmed | `v1` | `experiments/v1/config.yaml` | First formal baseline, CUB seed=5 H=73.93. |
| `GTPJ-v2` | owner_activated_unconfirmed | `v2` | `experiments/v2/config.yaml` | CLIP-A-self text prototype adapter, best_observed_H=74.29, confirmed_H=pending, based on TRIAL-001 / ATTEMPT-019. |
| `GTPJ-v3` | owner_accepted_stochastic_unconfirmed | `v3` | `experiments/v3/config.yaml` | Strict conditional FAE-memory JEPA, best_observed_H=74.27, confirmed_H=pending, based on TRIAL-002 / ATTEMPT-004. |
| `GTPJ-v4` | confirmed | `v4` | `experiments/v4/config.yaml` | Min3-confirmed tuned v3 configuration from `local-v3-054`, confirmed_H=74.45, best_observed_H=74.47. |
| `GTPJ-v5` | owner_activated_provisional | `v5` | `experiments/v5/config.yaml` | TRIAL-003 conditional BVSA text active mainline from `trial003-main100-069`; best_observed_H=74.54, confirmed_H=74.44; v4 remains confirmed reference. |

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
| `CONFIRM-001_local_v3_054_min3` | `v3` | `confirmation` | promote | `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3` | Server min3 H=74.46/74.42/74.47, confirmed_H=74.45; promoted to `GTPJ-v4`. |
