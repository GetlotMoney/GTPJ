# Project Status

Date: 2026-08-07

## 2026-08-07 V5 干净母版更新

`MODEL-V5-TEMPLATE-V1` 已在本地冻结：分支 `framework/v5-template-v1`、Tag
`model/v5-template-v1` 和代码提交 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`
完全一致。历史 `v5` Tag 仍指向 `08e5ecb1a5db6c6d589527cda35d8d4f7f437e07`，没有移动。

本地验证为 36 项 V5 专项测试、251 项工作流测试和 5 个结构检查全部通过，三名独立审核员均为 `ALLOW`。
这只证明代码路径与管理边界通过本地验证，不代表服务器 U/S/H/ZS 已经复跑确认。

`V5-ABLATION-001` 已从新母版重新绑定，独立分支为
`exp/v5/ablation/ablation-001-local-branch-effect`；现在是 6 行同种子配对矩阵，实验代码、真实配置、数据清单和服务器控制器均已完成。当前仍处于开跑前门禁阶段，strict-3 审核与最终冻结提交未完成前不会启动训练。

## 2026-08-06 管理结构更新

实验管理已切换为“同级正式框架 + 只读代码母版 + 四类独立实验 + 逐次运行表”。当前图形总览见
`docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V3.html`，正式规则见
`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。本阶段只改管理、校验和查看方式，没有改变模型、训练或评估结论。

| 层级 | 文件 | 现在负责什么 |
|---|---|---|
| 框架身份 | `experiments/vX/framework.yaml` | 说明这是哪个正式框架、历史上从哪个同级框架演变而来。 |
| 代码母版 | `experiments/vX/TEMPLATE.yaml` | 锁定母版编号、只读分支、Tag 和准确 commit。 |
| 实验起点 | `experiments/vX/<type>/<id>/EXPERIMENT.yaml` | 说明这项实验实际复制了哪份母版；实验之间不得接着叠代码。 |
| 真实运行 | `PARAMETER_MATRIX.csv` | 每一行记录一套参数、一个 seed、一次状态和结果。 |

V1、V2、V3 继续使用 `MODEL-VX-TEMPLATE-V0 / legacy_frozen` 历史母版账本，只解释过去，不能启动新实验。
V5 已改用 `MODEL-V5-TEMPLATE-V1 / frozen`；局部分支消融已经从该准确母版重新绑定，旧 Attempt 只保留为规划来源。

## Current Active Mainline

```text
name: GTPJ-v5
code_tag: v5
status: owner_activated_provisional
dataset: CUB GZSL
baseline_evidence: experiments/v5/baseline/
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
active_main_update: activated
future_tuning_base: config/versions/v5.yaml
```

`GTPJ-v5` is the owner-selected active mainline. It activates TRIAL-003 so that `all_text_cond` enters BVSA, including the cross/local_score branch, and freezes the best source configuration from the 100-run batch:

```text
source_run: RUN-20260630-0002-trial003-main100-2gpu
source_candidate: trial003-main100-069
pse_outer_ratio: 0.65
clip_a_self_outer_ratio: 0.65
local_weight: 0.2
```

## Confirmed Reference

```text
name: v3 CONFIRM-001 local-v3-054
code_tag: v3
status: confirmed_config
confirmed_H: 74.47
best_observed_H: 74.47
H_mean: 74.45
historical_tag: v4 (legacy config-only tag; not a formal framework version)
```

`v3/CONFIRM-001 local-v3-054` remains the stronger confirmed reference because its min3 cluster passed and the formal confirmed H is `74.47`; its repeat mean is `74.45`, while the v5 frozen-repeat mean is `74.44`. `GTPJ-v5` is active because the owner explicitly selected it as the next mainline for tuning, not because it supersedes the confirmed v3 config.

## 当前研究前沿（尚未晋级）

```text
trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
best_single_H: 75.11
best_single_ref: ATTEMPT-017 / DR-095
best_single_status: valid_single_run
latest_repeat_attempt: ATTEMPT-018
latest_repeat_best_H: 74.71
latest_repeat_mean_H: 74.58
latest_repeat_status: not_restored
promotion_decision: blocked
```

当前最高单次 `H=75.11` 来自 ATTEMPT-017 的 `DR-095 / a015dr035_weight_plus_0.01`，对应 `U=73.00`、`S=77.36`、`ZS=82.12`。ATTEMPT-018 对该配置完成 5 次同 seed exact repeat，结果为 `74.71/74.62/74.51/74.60/74.45`，均值 `74.58`，没有达到 `restore_target_H=75.11`。

### 高分候选分布

| 证据位置 | 已记录的高分分布 | 说明 |
|---|---|---|
| `ATTEMPT-004` | `75.02`、`75.00`、`74.90`、`74.90` | 早期 direction h48 高分单次；75.02 后续复现未回到来源水平。 |
| `ATTEMPT-011` | 选出的 12 个 `H>=74.80` 来源候选：`75.00×2`、`74.98`、`74.96`、`74.89`、`74.85`、`74.83`、`74.82×3`、`74.81`、`74.80` | 说明 direction h48 附近存在连续高分区域，而不是单个偶然配置。 |
| `ATTEMPT-014` | exact repeat top5：`74.99`、`74.93`、`74.92`、`74.88`、`74.87` | `74.99` 还原的是较低来源目标 `74.89`；两个来源为 75.00 的候选只达到 `74.81/74.80`。 |
| `ATTEMPT-015` | 100 jobs 中有 15 个 `H>=74.80`：`75.04`、`75.00`、`74.92`、`74.91`、`74.89`、`74.88×2`、`74.85`、`74.83`、`74.81×5`、`74.80` | 这是当前最清楚的密集高分带证据。 |
| `ATTEMPT-017` | 结果文件 top5：`75.11`、`74.92`、`74.90`、`74.86`、`74.86` | 机制窄消融产生当前最高单次，但随后未复现。 |

### 75 分来源的复现结论

| 来源单次 | 来源 | 后续 exact repeat | 结论 |
|---:|---|---|---|
| `75.11` | ATTEMPT-017 DR-095 | ATTEMPT-018，5 次，best `74.71`，mean `74.58` | `not_restored`，promotion blocked |
| `75.04` | ATTEMPT-015 DR-004 | ATTEMPT-016，5 次，best `74.84`，mean `74.66` | `not_restored` |
| `75.00` | ATTEMPT-015 DR-035 | ATTEMPT-016，5 次，best `74.85`，mean `74.65` | `not_restored` |
| `75.02` | ATTEMPT-004 DR-035 | ATTEMPT-007 min3 mean `74.61`；ATTEMPT-008 min6 mean `74.56`、best `74.76` | 扩展复现未确认，promotion blocked |

因此，项目可以公开陈述“最高单次达到 `H=75.11`，并存在密集的 `74.8x/74.9x` 候选带”，但不能陈述“confirmed/baseline 已达到 75”。

## Enabled Modules

- Frozen CLIP ViT-L/14@336px backbone
- GPT text description prototypes
- PSE / CLIP-A-self sentence-level text prototype adapter
- FGVD geometry-aware visual memory
- BVSA bidirectional visual-semantic alignment
- ICSA conditional text adaptation
- SGMP auxiliary training
- Conditional BVSA text routing: `all_text_cond [B, C, 768] -> BVSA cross/local_score`

## Formal Result Status

| Experiment | Dataset | Seed | U | S | H | ZS | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `GTPJ-v1` | CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | confirmed |
| `GTPJ-v2` | CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | owner activated, needs confirmation |
| `GTPJ-v3` | CUB GZSL | 5 | 71.22 | 77.60 | 74.27 | 81.38 | owner accepted stochastic, needs confirmation |
| `v3 CONFIRM-001 local-v3-054` | CUB GZSL | 5 | 71.53 | 77.66 | 74.47 | 81.25 | confirmed config under v3; H_mean=74.45 |
| `GTPJ-v5` | CUB GZSL | 5 | 72.00 | 77.07 | 74.44 | 81.56 | owner activated provisional active mainline |

## Known Risks

- `GTPJ-v5` has a best single repeat of `H=74.54`, but its 5-repeat mean is `H=74.44`, below the confirmed v3 config `confirmed_H=74.47`.
- Dynamic Routing trial 已出现 `H=75.11` 的研究单次和大量 `74.8x/74.9x` 候选，但 75.11、75.04、75.02、75.00 的关键来源均未在后续 exact repeat 中还原。
- Future manuscript-grade claims should cite whether a number is `confirmed_H`, repeat mean, or `best_observed_H`.
- The next tuning round should start from `config/versions/v5.yaml` but still compare against `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`.

## Warehouse Retention

2026-06-29 checkpoint retention has been applied on `lab4090`:

```text
manifest: /data/lby/projects/cv_project/GTPJ_Warehouse/retention/model_best_retention_20260629_v4.json
historical_policy_applied: 2026-06-29 run kept 5 best model_best/best-model checkpoints by H
current_workflow_policy: keep Top-3 best model_best/best-model checkpoints by H after each campaign
kept: 5
deleted: 199 training checkpoint files
deleted_bytes: 31055128358
excluded: logs, receipts, summaries, configs, manifests, registries, and data/cache feature tensors
```

## Next Steps

先完成 `V5-ABLATION-001` 的 strict-3 复核、运行时门和冻结提交，再在两张 GPU 上运行完整 V5 与代码级 `global_only` 的 3 个 seed 配对实验。
本轮只回答“彻底去掉局部分支后效果变化多大”；局部权重调参和其他模块消融在这组结果收口后另开独立实验项。
效果比较仍以 `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47` 为正式参考。
