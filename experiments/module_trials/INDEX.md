# Module Trials Index

Authoritative idea records live under `idea_tree/ideas/`. This directory stores implementation trials and lightweight evidence after an idea is selected and code work starts.

## Trial Records

| Idea | Source idea file | Trial evidence directory | Trial status | Summary |
|---|---|---|---|---|
| `IDEA-0001` | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly` | owner_activated_to_v2 | ATTEMPT-019 best_observed_H=74.29 is owner-activated as `GTPJ-v2`; clean confirmation and U/S gap review remain blocking follow-ups before confirmed/baseline-grade claims. |
| `IDEA-0002` | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-001_fae_memory_jepa` | revise | ATTEMPT-001 H=73.82, delta_H=-0.47 vs active v2 best_observed_H=74.29 (unconfirmed); do not promote/tag before v2 clean confirmation. |
| `IDEA-0002` | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa` | owner_accepted_to_v3 | ATTEMPT-004 H=74.27 accepted as `GTPJ-v3` by owner stochastic-variance decision; confirmed_H remains pending and seed-42 reruns are kept as variance evidence. |
| `IDEA-0002` | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text` | owner_activated_to_v5 | `all_text_cond` enters BVSA cross/local_score; main100 best repeat H=74.54 and frozen-repeat mean H=74.44; owner activated as `GTPJ-v5` active mainline. |
| `IDEA-0003` | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing` | revise | RUN-20260630-0005 completed 50/50; best dynamic single H=74.39 and repeat mean H=74.23 did not beat `v3/CONFIRM-001 local-v3-054` confirmed H=74.47 or v5 repeat mean H=74.44; no promotion, next profile focuses direction/local/PSE with ICSA fixed. |
## Start Rules

- Verify or explicitly record source status before any trial starts.
- Confirm the selected-version score in `idea_tree/versions/<base_version>.md`.
- Create the trial directory through the workflow helper.
- Keep a default-off path equivalent to the selected base version.
