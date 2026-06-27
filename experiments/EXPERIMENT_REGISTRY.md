# 实验登记表

项目：GTPJ

## 版本

| 版本 | 状态 | 代码 tag | 配置 | 说明 |
|---|---|---|---|---|
| `GTPJ-v1` | 已确认 | `v1` | `experiments/v1/config.yaml` | 新仓库第一版正式 baseline，CUB seed=5 H=73.93。 |
| `GTPJ-v2` | owner_activated_unconfirmed | `v2` | `experiments/v2/config.yaml` | CLIP-A-self text prototype adapter 主线版，CUB seed=5 best_observed_H=74.29，confirmed_H=pending，基于 TRIAL-001 / ATTEMPT-019。 |

## 模块 Trials

| Trial | Idea | Status | Directory | Note |
|---|---|---|---|---|
| `TRIAL-001_clip_a_self_residual_seenonly` | `IDEA-0001` | owner_activated_to_v2 | `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly` | ATTEMPT-019 best_observed_H=74.29 is owner-activated as `GTPJ-v2`; clean confirmation and U/S gap review remain blocking follow-ups before baseline-grade claims. |

## 版本实验

| 实验 | 版本 | 类型 | 状态 | 目录 | 说明 |
|---|---|---|---|---|---|
| `CONFIRM-001_v1_seed5` | `v1` | `confirmation` | keep | `experiments/v1/confirmation/CONFIRM-001_v1_seed5` | H=73.77, delta_H=-0.16; Warehouse artifacts registered. |
