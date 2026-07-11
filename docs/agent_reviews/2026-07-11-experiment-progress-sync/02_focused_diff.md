# Focused Diff

本文件是给 Claude Code 默认读取的精简 diff。完整证据仍保留在 `02_diff.patch`。

## Changed Files

- NEXT_ACTIONS.md
- README.md
- docs/PROJECT_STATUS.md
- experiments/README.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml
- experiments/module_trials/INDEX.md
- idea_tree/idea_tree.json
- idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
- idea_tree/queues/queue_state.yaml
- idea_tree/versions/v5.md
- workflow/README.md

## Diff Stat

```text
 NEXT_ACTIONS.md                                    |  6 ++--
 README.md                                          | 18 ++++++++++
 docs/PROJECT_STATUS.md                             | 40 ++++++++++++++++++++-
 experiments/README.md                              |  2 ++
 .../TRIAL-001_dynamic-routing/README.md            | 42 +++++++++++++++++-----
 .../TRIAL-001_dynamic-routing/quality_check.md     | 16 +++++----
 .../TRIAL-001_dynamic-routing/result.md            | 19 +++++++---
 .../TRIAL-001_dynamic-routing/result.yaml          | 20 ++++++++---
 experiments/module_trials/INDEX.md                 |  2 +-
 idea_tree/idea_tree.json                           | 14 ++++----
 .../IDEA-0003_dynamic_residual_routing/IDEA.md     | 28 +++++++--------
 idea_tree/queues/queue_state.yaml                  |  6 ++--
 idea_tree/versions/v5.md                           |  4 +--
 workflow/README.md                                 |  2 +-
 14 files changed, 163 insertions(+), 56 deletions(-)
```

## Focused Patch

```diff
diff --git a/NEXT_ACTIONS.md b/NEXT_ACTIONS.md
index 08dba8c..900c237 100644
--- a/NEXT_ACTIONS.md
+++ b/NEXT_ACTIONS.md
@@ -1,26 +1,26 @@
 # GTPJ 当前待办

 这是当前执行窗口，只保留近期优先动作；完整创意库不放在这里。

 - 当前关注：GTPJ-v5 active mainline 后的近期复现、调参、队列整理和证据收尾。
 - 管理规则：只保留 3-7 条近期动作；完整创意库看 idea_tree/INDEX.md；具体实验动作写入 task/trial/attempt。
-- 更新时间：2026-07-04
+- 更新时间：2026-07-11

 ## 当前窗口

 | 优先级 | 事项 | 类型 | 负责人 | 状态 | 阻塞 | 证据位置 |
 | --- | --- | --- | --- | --- | --- | --- |
-| P0 | 每次正式 campaign 结束后执行 Warehouse checkpoint retention，只保留 Top-5 best model_best/best-model files 并记录 manifest。 | artifact_retention | Coordinator | open | - | docs/workflow/reference/artifact_policy.md |
+| P0 | 每次正式 campaign 结束后执行 Warehouse checkpoint retention，只保留 Top-3 best model_best/best-model files 并记录 manifest。 | artifact_retention | Coordinator | open | - | docs/workflow/reference/artifact_policy.md |
 | P1 | 继续 v5-based tuning 或 ablation，配置来源必须是 config/versions/v5.yaml。 | tune_or_ablation | Coordinator | open | 需要 owner 指定调参、消融或混合实验范围。 | experiments/v5/ |
-| P1 | 下一轮调参后，用 repeat mean 判断 v5 是否超过 v4 confirmed_H=74.45。 | confirmation_planning | Coordinator | open | 需要先产生新的候选结果。 | experiments/v5/confirmation/ |
+| P1 | 下一轮调参后，用 repeat mean 判断 v5 是否超过 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47。 | confirmation_planning | Coordinator | open | 需要先产生新的候选结果。 | experiments/v5/confirmation/ |

 ## 已完成摘要

 | 事项 | 证据位置 |
 | --- | --- |
 | 初始化 GTPJ repository 和 workflow helper。 | docs/PROJECT_STRUCTURE.md |
 | 建立 GTPJ-v1 第一版正式 baseline，CUB seed=5 H=73.93。 | experiments/v1/baseline/result.yaml |
 | 记录 GTPJ-v2 owner-activated，best_observed_H=74.29，confirmed_H pending。 | experiments/v2/baseline/result.yaml |
 | 记录 GTPJ-v3 owner-accepted stochastic，best_observed_H=74.27，confirmed_H pending。 | experiments/v3/baseline/result.yaml |
 | 确认 local-v3-054 server min3：H=74.46 / 74.42 / 74.47。 | experiments/v4/baseline/result.yaml |
 | 激活 TRIAL-003 best conditional-BVSA-text candidate 为 GTPJ-v5 active mainline。 | experiments/v5/VERSION.md |
diff --git a/README.md b/README.md
index 2831d37..c27e9e6 100644
--- a/README.md
+++ b/README.md
@@ -8,24 +8,42 @@ code_tag: v5
 status: owner_activated_provisional
 best_observed_H: 74.54
 confirmed_H: 74.44
 source: TRIAL-003 main100 trial003-main100-069
 active_main_update: activated
 future_tuning_base: config/versions/v5.yaml
 ```

 `GTPJ-v5` is the active mainline selected by the owner on 2026-06-30. It activates the TRIAL-003 conditional BVSA text path, so `all_text_cond [B, C, 768]` enters BVSA, including the cross/local_score branch.

 The stronger confirmed reference is `v3 / CONFIRM-001 local-v3-054 / confirmed_H=74.47`. v5 is active for the next tuning round, but its frozen-repeat mean is `74.44`, so it is not a stronger confirmed-baseline claim over that confirmed v3 config.

+## 当前研究前沿（尚未晋级）
+
+```text
+research_trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
+research_best_single_H: 75.11
+research_best_single_ref: ATTEMPT-017 / DR-095
+research_best_restore_status: not_restored
+latest_exact_repeat: ATTEMPT-018
+latest_repeat_best_H: 74.71
+latest_repeat_mean_H: 74.58
+confirmed_reference_H: 74.47
+promotion_decision: blocked
+```
+
+`H=75.11` 是当前仓库记录的最高单次结果，但它属于调参/窄消融单次证据，不是 confirmed 结果。随后 5 次同配置、同 seed 的 exact repeat 均未还原该数值，因此不能把正式 baseline 或 `confirmed_H` 写成 75.11。
+
+高分并非孤立点：历史账本还记录了 `75.04`、`75.02`、多次 `75.00`，以及一批 `74.80–74.99` 候选。完整分布、候选身份和复现结论见[项目状态](docs/PROJECT_STATUS.md)与[动态路由 trial 进展](experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md)。
+
 ## Versions

 | Version | Code tag | Status | Dataset | Note |
 |---|---|---|---|---|
 | `GTPJ-v1` | `v1` | confirmed | CUB GZSL | First formal baseline, seed=5, H=73.93. |
 | `GTPJ-v2` | `v2` | owner activated, needs confirmation | CUB GZSL | CLIP-A-self text prototype adapter, best_observed_H=74.29. |
 | `GTPJ-v3` | `v3` | owner accepted stochastic, needs confirmation | CUB GZSL | Strict conditional FAE-memory JEPA, best_observed_H=74.27. |
 | `GTPJ-v4` | `v4` | legacy config-only tag | CUB GZSL | Historical misclassification of `v3/CONFIRM-001 local-v3-054`; not a formal framework version. |
 | `GTPJ-v5` | `v5` | owner activated provisional active mainline | CUB GZSL | TRIAL-003 conditional BVSA text, best_observed_H=74.54, repeat mean H=74.44. |

 Version tree:

diff --git a/docs/PROJECT_STATUS.md b/docs/PROJECT_STATUS.md
index 68a7349..396f6dc 100644
--- a/docs/PROJECT_STATUS.md
+++ b/docs/PROJECT_STATUS.md
@@ -1,15 +1,15 @@
 # Project Status

-Date: 2026-06-30
+Date: 2026-07-11

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
@@ -32,48 +32,86 @@ local_weight: 0.2
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

+## 当前研究前沿（尚未晋级）
+
+```text
+trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
+best_single_H: 75.11
+best_single_ref: ATTEMPT-017 / DR-095
+best_single_status: valid_single_run
+latest_repeat_attempt: ATTEMPT-018
+latest_repeat_best_H: 74.71
+latest_repeat_mean_H: 74.58
+latest_repeat_status: not_restored
+promotion_decision: blocked
+```
+
+当前最高单次 `H=75.11` 来自 ATTEMPT-017 的 `DR-095 / a015dr035_weight_plus_0.01`，对应 `U=73.00`、`S=77.36`、`ZS=82.12`。ATTEMPT-018 对该配置完成 5 次同 seed exact repeat，结果为 `74.71/74.62/74.51/74.60/74.45`，均值 `74.58`，没有达到 `restore_target_H=75.11`。
+
+### 高分候选分布
+
+| 证据位置 | 已记录的高分分布 | 说明 |
+|---|---|---|
+| `ATTEMPT-004` | `75.02`、`75.00`、`74.90`、`74.90` | 早期 direction h48 高分单次；75.02 后续复现未回到来源水平。 |
+| `ATTEMPT-011` | 选出的 12 个 `H>=74.80` 来源候选：`75.00×2`、`74.98`、`74.96`、`74.89`、`74.85`、`74.83`、`74.82×3`、`74.81`、`74.80` | 说明 direction h48 附近存在连续高分区域，而不是单个偶然配置。 |
+| `ATTEMPT-014` | exact repeat top5：`74.99`、`74.93`、`74.92`、`74.88`、`74.87` | `74.99` 还原的是较低来源目标 `74.89`；两个来源为 75.00 的候选只达到 `74.81/74.80`。 |
+| `ATTEMPT-015` | 100 jobs 中有 15 个 `H>=74.80`：`75.04`、`75.00`、`74.92`、`74.91`、`74.89`、`74.88×2`、`74.85`、`74.83`、`74.81×5`、`74.80` | 这是当前最清楚的密集高分带证据。 |
+| `ATTEMPT-017` | 结果文件 top5：`75.11`、`74.92`、`74.90`、`74.86`、`74.86` | 机制窄消融产生当前最高单次，但随后未复现。 |
+
+### 75 分来源的复现结论
+
+| 来源单次 | 来源 | 后续 exact repeat | 结论 |
+|---:|---|---|---|
+| `75.11` | ATTEMPT-017 DR-095 | ATTEMPT-018，5 次，best `74.71`，mean `74.58` | `not_restored`，promotion blocked |
+| `75.04` | ATTEMPT-015 DR-004 | ATTEMPT-016，5 次，best `74.84`，mean `74.66` | `not_restored` |
+| `75.00` | ATTEMPT-015 DR-035 | ATTEMPT-016，5 次，best `74.85`，mean `74.65` | `not_restored` |
+| `75.02` | ATTEMPT-004 DR-035 | ATTEMPT-007 min3 mean `74.61`；ATTEMPT-008 min6 mean `74.56`、best `74.76` | 扩展复现未确认，promotion blocked |
+
+因此，项目可以公开陈述“最高单次达到 `H=75.11`，并存在密集的 `74.8x/74.9x` 候选带”，但不能陈述“confirmed/baseline 已达到 75”。
+
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
+- Dynamic Routing trial 已出现 `H=75.11` 的研究单次和大量 `74.8x/74.9x` 候选，但 75.11、75.04、75.02、75.00 的关键来源均未在后续 exact repeat 中还原。
 - Future manuscript-grade claims should cite whether a number is `confirmed_H`, repeat mean, or `best_observed_H`.
 - The next tuning round should start from `config/versions/v5.yaml` but still compare against `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`.

 ## Warehouse Retention

 2026-06-29 checkpoint retention has been applied on `lab4090`:

 ```text
 manifest: /data/lby/projects/cv_project/GTPJ_Warehouse/retention/model_best_retention_20260629_v4.json
 historical_policy_applied: 2026-06-29 run kept 5 best model_best/best-model checkpoints by H
 current_workflow_policy: keep Top-3 best model_best/best-model checkpoints by H after each campaign
 kept: 5
diff --git a/experiments/README.md b/experiments/README.md
index d1f8006..a8e70a2 100644
--- a/experiments/README.md
+++ b/experiments/README.md
@@ -10,24 +10,26 @@ EXPERIMENT_REGISTRY.md   全局实验登记表
 module_trials/           有代码实现证据的创新 trial
 v1/                      GTPJ-v1 baseline、tune、ablation、confirmation 记录
 v2/                      GTPJ-v2 baseline、tune、ablation、confirmation 记录
 v3/                      GTPJ-v3 baseline、tune、ablation、confirmation 记录
 v4/                      historical config-only tag record; formal reference is v3/CONFIRM-001
 v5/                      GTPJ-v5 owner-activated active mainline 记录
 ```

 当前 active mainline code 是 `GTPJ-v5 / tag v5`。`GTPJ-v5` 是 owner-activated provisional，`best_observed_H=74.54`，5 次 frozen repeat mean `confirmed_H=74.44`。

 当前更强的 confirmed reference 是 `v3/CONFIRM-001 local-v3-054 / confirmed_H=74.47`。历史 `v4` tag 是 config-only 误分类，不作为正式框架版本。

+当前研究最高单次来自 `IDEA-0003/TRIAL-001 ATTEMPT-017`，`H=75.11`；ATTEMPT-018 的 5 次 exact repeat 最好 `H=74.71`、均值 `H=74.58`，未还原，因此该结果仍是未晋级的研究单次，不能替代 confirmed reference。完整高分分布见该 trial 的 [README](module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md) 和 [ATTEMPTS](module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md)。
+
 旧的 `experiments/v1/` 到 `experiments/v4/` 不删除。`main` 保存全部版本账本，代码快照靠对应 tag 回滚。

 ## 正式表格地图

 以后查询“现在有哪些待跑实验”，先看正式表格，不从 `.gtpj_runtime/` 目录反推。

 | 问题 | 先看哪张表 | 说明 |
 |---|---|---|
 | 全局有哪些版本和已登记实验 | `EXPERIMENT_REGISTRY.md` | 全局索引，辅助定位，不替代各类型正式表格。 |
 | 某个 baseline 的调参待跑 | `vX/tune/INDEX.md` | `Status` 为 `planned/pending/pre_run/pre_run_gated/ready_to_run` 的行是正式待跑。 |
 | 某个 baseline 的消融待跑 | `vX/ablation/INDEX.md` | 同上。 |
 | 某个 baseline 的复现/确认待跑 | `vX/confirmation/INDEX.md` | 同上。 |
diff --git a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md
index a9dbec3..0f49658 100644
--- a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md
+++ b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md
@@ -3,45 +3,69 @@
 ```text
 trial_id: TRIAL-001
 idea_id: IDEA-0003
 base_version: v5
 base_code_tag: v5
 branch_source: main
 idea_source_file: idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
 idea_title: Dynamic Residual Routing
 version_score: 82.0
 applicability: direct
 code_branch: dev/v5-idea-0003-trial-001-dynamic-routing
 run_code_commit: d49f60849b498a0aa6539bb245a2389ffabf2941
-trial_decision: rerun
+trial_decision: revise
 promotion_decision: blocked
 promote_to:
 evidence_level: valid_single_run
-best_observed_H: 75.04
-best_dynamic_single_H: 75.02
-best_dynamic_repeat_mean_H: 74.61
+best_observed_H: 75.11
+best_dynamic_single_H: 75.11
+best_fixed_n_repeat_mean_H: 74.63
+best_fixed_n_repeat_mean_ref: ATTEMPT-011 / DR047 / n=10
+latest_exact_repeat_ref: ATTEMPT-018 / A017DR095 / n=5
+latest_exact_repeat_best_H: 74.71
+latest_exact_repeat_mean_H: 74.58
+latest_exact_repeat_status: not_restored
 confirmed_H: pending
-confirmation_status: needs_confirmation
+confirmation_status: not_restored
 changed_files: model/MyModel.py; train_GTPJ_CUB.py; workflow/gtpj_workflow.py; tests/test_fae_memory_jepa.py; tests/test_gtpj_workflow.py; trial ledger/config
 run_config:
 attempts: ATTEMPTS.md
 manifest: manifest.yaml
 result_yaml: result.yaml
 result_md: result.md
 quality_check: quality_check.md
 agent_summary: agent_summary.md
 implementation: implementation.md
 ```

-## Run Summary
+## 当前实验前沿
+
+当前最高单次是 ATTEMPT-017 `DR-095 / a015dr035_weight_plus_0.01`：`H=75.11`、`U=73.00`、`S=77.36`、`ZS=82.12`。该结果是 `valid_single_run`，不是 confirmation 或 promotion 证据。
+
+ATTEMPT-018 已完成同配置、同 seed 的 5 次 exact repeat，最好 `H=74.71`、均值 `H=74.58`、范围 `74.45–74.71`，没有达到 `restore_target_H=75.11`，状态为 `stopped_repeat_unstable / not_restored`。
+
+| 分层 | 代表结果 | 证据解释 |
+|---|---|---|
+| 最高搜索单次 | ATTEMPT-017 DR-095 `H=75.11` | 当前最高，但未复现。 |
+| 其他 75 分单次 | ATTEMPT-015 `75.04/75.00`；ATTEMPT-004 `75.02/75.00`；ATTEMPT-011 `75.00×2` | 都只能作为调参信号。 |
+| 74.9x 前沿 | `74.99/74.98/74.96/74.93/74.92/74.91/74.90` | 分布在 ATTEMPT-011、014、015、017，说明 h48 小 anchor 区域存在连续信号。 |
+| 74.8x 密集带 | ATTEMPT-015 单轮有 11 个 `74.80–74.89` job；ATTEMPT-011 选出的来源候选中有 8 个 `74.80–74.89` | 高分不是只有一个点，但仍缺少稳定 75+ 复现。 |
+| 最佳固定次数重复均值 | ATTEMPT-011 DR047，`n=10`，mean `74.630`，best `74.87` | 高于旧的 ATTEMPT-007 min3 mean `74.61`，仍非 75+ confirmation。 |
+| 较低目标还原 | ATTEMPT-014 DR-022 `H=74.99`，来源目标 `74.89` | 证明较低目标可还原，不等于还原 75。 |
+
+当前结论保持：`promotion_decision: blocked`；正式 confirmed reference 仍是 `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`。
+
+## ATTEMPT-001 初始运行摘要
+
+以下 ATTEMPT-001/002/004/006 段落保留历史阶段判断；当前结论以本文开头“当前实验前沿”和 `ATTEMPTS.md` 为准。

 | Field | Value |
 |---|---|
 | Server run | `RUN-20260630-0005-dynroute50-2gpu` |
 | Runtime path | `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260630-0005-dynroute50-2gpu` |
 | Warehouse summary path | `/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/batch-RUN-20260630-0005-dynroute50-2gpu` |
 | Jobs | 50 completed / 0 failed |
 | GPU plan | two controllers on GPU0/GPU1 |
 | Batch profile | `balanced-aggressive` |
 | Analysis command | `python workflow/gtpj_workflow.py analyze-dynamic-routing-batch --run-dir %TEMP%/gtpj-RUN-20260630-0005-dynroute50-2gpu --top-k 12` |

 ## Dynamic Routes Tested
@@ -82,25 +106,25 @@ Repeat means:
 | DR-008 local_class_h24 | 5 | 74.23 | 68.54 | 80.97 | below v4/v5 references; U weak |

 Group summary:

 | Group | n | Mean H | Best H | Interpretation |
 |---|---:|---:|---:|---|
 | `direction_gate` | 6 | 74.10 | 74.38 | best follow-up direction; strong U balance |
 | `local_gate` | 8 | 73.60 | 74.39 | close single-run result but repeat mean did not hold |
 | `pse_gate` | 6 | 73.61 | 73.86 | stable but not competitive |
 | `icsa_gate` | 8 | 53.64 | 62.88 | collapsed or over-injected; avoid dynamic ICSA for now |
 | `combination` | 8 | 57.32 | 73.38 | combinations are too unstable in this profile |

-## Decision
+## ATTEMPT-001 当时决策

 `promotion_decision: rejected`.

 The best dynamic single result, DR-008 at H=74.39, did not beat `v3/CONFIRM-001 local-v3-054` confirmed H=74.47 or v5 repeat mean H=74.44. The repeated dynamic candidate averaged H=74.23 and had a low U mean. The static control also did not exceed references.

 `trial_decision: revise`.

 Follow-up work should keep ICSA fixed, prioritize direction/local/PSE gates, and use the `principled-followup` batch profile that was added after this run.

 ## Follow-Up Attempt Status

 ATTEMPT-002 tested a deliberate `batch_size=128` intervention with two 50-job
@@ -121,27 +145,27 @@ ATTEMPT-002 summary artifacts:
 - `runtime:v5:module_trial:TRIAL-001:RUN-20260701-0008:summary` -> `lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260701-0008-dynroute-bs128-bold50-2gpu/summary.csv`

 ## Integrated ATTEMPT-004 / Workflow-v2 Status

 ATTEMPT-004 and the workflow-v2 validation campaign refine the ATTEMPT-003 direction-gate signal.

 | Source | Run | Best job | Name | H | U | S | Decision |
 |---|---|---|---|---:|---:|---:|---|
 | ATTEMPT-004 | `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | DR-035 | `direction_sample_h48_w0.525_a0.005` | 75.02 | 72.69 | 77.51 | repeat first |
 | ATTEMPT-004 | `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | DR-009 | `dr016_direction_sample_h48_w0.45_a0.003_r02` | 75.00 | 72.93 | 77.19 | supporting single |
 | ATTEMPT-006 | `RUN-20260702-0003-mixed2innov8tune-2gpu` | TUNE-002 / DR-004 | `tune_direction_h48_w0.525_a0.003` | 74.75 | 72.90 | 76.69 | repeat candidate |

-Current interpretation:
+ATTEMPT-004/006 当时解释（已被后续 ATTEMPT-017/018 证据更新）：

-- Best observed single is ATTEMPT-004 DR-035 H=75.02.
+- 当时最高单次是 ATTEMPT-004 DR-035 H=75.02；当前最高单次已更新为 ATTEMPT-017 H=75.11。
 - The strongest family is `direction_sample`, hidden 48, anchor lambda around 0.003-0.005.
 - ATTEMPT-006 workflow-v2 innovation probes did not help and are stopped for this campaign.
 - No result is confirmed; promotion remains blocked until min3 repeat and post-run quality closeout.

 Integrated report:

 - `experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/FINAL_REPORT.md`
 - `attempts/ATTEMPT-006/result.yaml`

 ## Checkpoint Retention

 The server Warehouse was pruned according to the workflow rule "keep only the best 3 model checkpoints after each experiment batch." The retained checkpoints are:
diff --git a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md
index b51de16..2bba237 100644
--- a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md
+++ b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md
@@ -1,32 +1,36 @@
 # TRIAL-001 Quality Check

 ```text
 quality_check_mode: STRICT
 attempt_id: ATTEMPT-017
-decision: PASS_RERUN
+latest_repeat_attempt: ATTEMPT-018
+decision: PASS_REVISE
+decision_scope: current trial after ATTEMPT-018 exact repeat closeout
+latest_trial_decision: revise
 promotion_decision: blocked
 evidence_level: valid_single_run
 ```

 ## Findings

-- Metrics are synchronized from `ATTEMPT-017`: U=73.00, S=77.36, H=75.11, ZS=82.12, best_epoch=48.
-- Trial-level decision recorded as `rerun`.
-- Attempt confirmation status: confirmed_H=pending, confirmation_status=needs_confirmation.
-- Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
+- 最高单次来自 `ATTEMPT-017`：U=73.00、S=77.36、H=75.11、ZS=82.12、best_epoch=48。
+- `ATTEMPT-018` 已完成 5 次 exact repeat：best H=74.71、mean H=74.58，未达到 restore_target_H=75.11。
+- Trial-level decision 记录为 `revise`，confirmation_status 为 `not_restored`。
+- Promotion/tag 保持 blocked；H=75.11 只能作为未还原的研究单次。
 - Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

 ## Artifact Check

 - [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv` exists in Warehouse.
 - [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl` exists in Warehouse.
 - [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json` exists in Warehouse.
 - [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl` exists in Warehouse.
 - [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json` exists in Warehouse.
 - [x] `artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json` exists in Warehouse.
 - [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
+- [x] `attempts/ATTEMPT-018/manifest.yaml`、`result.yaml`、`quality_check.md` 记录了最新 exact repeat 非还原结论。
 - [x] No raw training log or checkpoint is copied into GitHub.

 ## Decision

-PASS_RERUN.
+PASS_REVISE；ATTEMPT-017 保留为最高单次来源，ATTEMPT-018 的复现结论为 `not_restored`，当前 trial decision 为 `revise`。
diff --git a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md
index ad7748a..c231480 100644
--- a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md
+++ b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md
@@ -2,30 +2,41 @@

 ## Metrics

 | Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
 |---|---|---|---:|---:|---:|---:|---:|---:|---:|
 | ATTEMPT-017 | v5 | CUB | 5 | 73.00 | 77.36 | 75.11 | 82.12 | 48 | +0.57 |

 ## Evidence

 ```text
 trial_id: TRIAL-001
 attempt_id: ATTEMPT-017
+attempt_role: selected_best_single
+current_trial_state_source: ATTEMPT-018
 evidence_level: valid_single_run
-result_status: rerun
+result_status: revise
 promotion_decision: blocked
 confirmed_H: pending
-confirmation_status: needs_confirmation
+confirmation_status: not_restored
+latest_exact_repeat_attempt: ATTEMPT-018
+latest_confirmation_status: not_restored
+latest_trial_decision: revise
 server_summary_csv_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv
 server_summary_jsonl_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl
 server_batch_status_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json
 server_events_jsonl_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl
 server_status_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json
 server_plan_json_artifact_id: artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json
 ```

 ## Decision

-`rerun`
+`revise`

-ATTEMPT-017 is recorded as `valid_single_run` with confirmed_H=pending and confirmation_status=needs_confirmation. Promotion/tag remains blocked because active v5 comparison reference is unconfirmed: v5 best_observed_H=74.54 (unconfirmed), confirmed_H=74.44.
+ATTEMPT-017 保留为 `valid_single_run` 最高单次来源；ATTEMPT-018 已完成 hard cap 内的 5 次 exact repeat，因此 trial 当前状态为 `revise/not_restored`，promotion/tag 继续 blocked。ATTEMPT-017 当时的 `rerun/needs_confirmation` 历史 decision 保留在 attempt-local 文件中。
+
+## 最新 exact repeat 结论
+
+ATTEMPT-018 对 ATTEMPT-017 `DR-095 / H=75.11` 完成 5 次同配置、同 seed exact repeat：`74.71/74.62/74.51/74.60/74.45`，最好 `74.71`、均值 `74.58`。没有一次达到 `restore_target_H=75.11`，且最好结果低于 near-miss 阈值 `74.91`。
+
+因此 `H=75.11` 继续作为当前 `best_observed_H` 单次记录保留，但状态是 `not_restored`；它不能更新 `confirmed_H`，也不能触发 promotion。
diff --git a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml
index 4d45c75..3af4332 100644
--- a/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml
+++ b/experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml
@@ -1,18 +1,20 @@
 schema_version: gtpj-result/v1
 experiment_id: "TRIAL-001"
 experiment_name: "TRIAL-001_dynamic-routing"
 kind: "module-trial"
 version: "v5"
 attempt_id: "ATTEMPT-017"
+attempt_role: "selected_best_single"
+current_trial_state_source: "ATTEMPT-018"
 metrics:
   U: "73.00"
   S: "77.36"
   H: "75.11"
   ZS: "82.12"
   best_epoch: "48"
   baseline_H: "74.54"
   baseline_reference: "best_observed_H"
   delta_H: "+0.57"
   seed: "5"
   source: "attempt_result_yaml"
   metric_semantics: "GZSL U/S/H/ZS from protected evaluator"
@@ -21,38 +23,48 @@ baseline:
   H: "74.54"
   reference_field: "best_observed_H"
   reference_status: "owner_activated_provisional"
   confirmed_H: "74.44"
   confirmation_status: "owner_activated_provisional"
 delta:
   H: "+0.57"
 run:
   seed: "5"
   pre_run_freeze_commit: ""
   command: ""
 decision:
-  status: "rerun"
-  result_status: "rerun"
+  status: "revise"
+  result_status: "revise"
   promotion_decision: "blocked"
   promote_to: ""
 evidence:
   evidence_level: "valid_single_run"
-  best_observed_H: "75.04"
+  best_observed_H: "75.11"
+  best_observed_ref: "ATTEMPT-017/DR-095"
+  best_observed_evidence_level: "valid_single_run"
+  best_observed_restore_status: "not_restored"
   confirmed_H: "pending"
-  confirmation_status: "needs_confirmation"
+  confirmation_status: "not_restored"
+  latest_exact_repeat_attempt: "ATTEMPT-018"
+  latest_exact_repeat_best_H: "74.71"
+  latest_exact_repeat_mean_H: "74.58"
+  latest_exact_repeat_status: "not_restored"
+  latest_trial_decision: "revise"
+  latest_result_status: "stopped_repeat_unstable"
   server_summary_csv_artifact_id: "artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-csv"
   server_summary_jsonl_artifact_id: "artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:summary-jsonl"
   server_batch_status_json_artifact_id: "artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:batch-status-json"
   server_events_jsonl_artifact_id: "artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:events-jsonl"
   server_status_json_artifact_id: "artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:server-status-json"
   server_plan_json_artifact_id: "artifact:v5:module_trial:TRIAL-001:ATTEMPT-017:RUN-20260709-0001:plan-json"
   manifest: "manifest.yaml"
   attempt_manifest: "attempts/ATTEMPT-017/manifest.yaml"
   label_mapping_id: "standard_v1"
   split_id: "standard_v1"
   class_order_id: "standard_v1"
 quality:
   manifest_verified: "true"
   boundary_audit_passed: "true"
   interface_contract_checked: "true"
   evaluation_semantics_verified: "true"
 recorded_at: "2026-07-09T03:35:52+00:00"
+progress_synced_at: "2026-07-11"
diff --git a/experiments/module_trials/INDEX.md b/experiments/module_trials/INDEX.md
index d00f599..15a8702 100644
--- a/experiments/module_trials/INDEX.md
+++ b/experiments/module_trials/INDEX.md
@@ -1,19 +1,19 @@
 # Module Trials Index

 Authoritative idea records live under `idea_tree/ideas/`. This directory stores implementation trials and lightweight evidence after an idea is selected and code work starts.

 ## Trial Records

 | Idea | Source idea file | Trial evidence directory | Trial status | Summary |
 |---|---|---|---|---|
 | `IDEA-0001` | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | `experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly` | owner_activated_to_v2 | ATTEMPT-019 best_observed_H=74.29 is owner-activated as `GTPJ-v2`; clean confirmation and U/S gap review remain blocking follow-ups before confirmed/baseline-grade claims. |
 | `IDEA-0002` | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-001_fae_memory_jepa` | revise | ATTEMPT-001 H=73.82, delta_H=-0.47 vs active v2 best_observed_H=74.29 (unconfirmed); do not promote/tag before v2 clean confirmation. |
 | `IDEA-0002` | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa` | owner_accepted_to_v3 | ATTEMPT-004 H=74.27 accepted as `GTPJ-v3` by owner stochastic-variance decision; confirmed_H remains pending and seed-42 reruns are kept as variance evidence. |
 | `IDEA-0002` | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | `experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text` | owner_activated_to_v5 | `all_text_cond` enters BVSA cross/local_score; main100 best repeat H=74.54 and frozen-repeat mean H=74.44; owner activated as `GTPJ-v5` active mainline. |
-| `IDEA-0003` | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing` | rerun | ATTEMPT-017 H=75.11, delta_H=+0.57 vs active v5 best_observed_H=74.54 (unconfirmed); do not promote/tag before v5 clean confirmation. |
+| `IDEA-0003` | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing` | revise | ATTEMPT-017 最高单次 H=75.11；ATTEMPT-018 exact repeat 5 次 best H=74.71、mean H=74.58，未还原；同一候选已到 5 次 hard cap，promotion blocked。 |
 ## Start Rules

 - Verify or explicitly record source status before any trial starts.
 - Confirm the selected-version score in `idea_tree/versions/<base_version>.md`.
 - Create the trial directory through the workflow helper.
 - Keep a default-off path equivalent to the selected base version.
diff --git a/idea_tree/idea_tree.json b/idea_tree/idea_tree.json
index 808fbee..9a53b73 100644
--- a/idea_tree/idea_tree.json
+++ b/idea_tree/idea_tree.json
@@ -128,25 +128,25 @@
         },
         "v4": {
           "score": 74,
           "applicability": "direct",
           "stage": "validated",
           "rationale": "Inherited by GTPJ-v4 from GTPJ-v3; v4 promotes a min3-confirmed tuned configuration and does not introduce a new IDEA-0002 code path.",
           "blockers": []
         },
         "v5": {
           "score": 76,
           "applicability": "direct",
           "stage": "validated",
-          "rationale": "TRIAL-003 extends IDEA-0002 by routing all_text_cond into BVSA cross/local_score. Owner activated the best main100 candidate as GTPJ-v5; v4 remains the stronger confirmed reference by repeat mean.",
+          "rationale": "TRIAL-003 通过把 all_text_cond 路由到 BVSA cross/local_score 扩展 IDEA-0002。Owner 已把 main100 最佳候选激活为 GTPJ-v5；更强的正式 confirmed reference 是 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47。",
           "blockers": []
         }
       },
       "base_versions": [
         "v2",
         "v3",
         "v4",
         "v5"
       ],
       "based_on_modules": [
         "GTPJ-v2 AG-JEPA",
         "FAE geometry-aware visual memory",
@@ -206,66 +206,66 @@
           "type": "version",
           "ref": "experiments/v3/VERSION.md",
           "note": "Owner accepted TRIAL-002 as GTPJ-v3 with stochastic variance explicitly preserved; confirmed_H remains pending."
         },
         {
           "type": "trial",
           "ref": "experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text/result.yaml",
           "note": "TRIAL-003 routes all_text_cond into BVSA; main100 best_observed_H=74.54, repeat mean H=74.44, owner activated as GTPJ-v5."
         },
         {
           "type": "version",
           "ref": "experiments/v5/VERSION.md",
-          "note": "GTPJ-v5 is the active mainline for future tuning; v4 confirmed_H=74.45 remains the confirmed reference."
+          "note": "GTPJ-v5 是后续调参的 active mainline；正式 confirmed reference 是 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47。"
         }
       ]
     },
     {
       "idea_id": "IDEA-0003",
       "idea_dir": "idea_tree/ideas/IDEA-0003_dynamic_residual_routing/",
       "title": "Dynamic Residual Routing",
       "status": "weakened",
       "source_type": "user",
       "source_ref": "owner:2026-06-30:make residual and mixture coefficients dynamic routes",
       "source_status": "local_heuristic",
       "global_score": 78.0,
       "core_summary": "把 v5 中固定 residual/mix 系数改成可学习 dynamic gates，按样本或类别调节 local、ICSA、BVSA direction 和 PSE routing。",
       "version_scores": {
         "v5": {
           "score": 82.0,
           "applicability": "direct",
           "stage": "trialing",
-          "rationale": "GTPJ-v5 already has fixed residual and mixture coefficients on the same active path: local_weight, icsa_ratio, weight_s2v, and pse_outer_ratio. TRIAL-001 ATTEMPT-001 completed 50/50 jobs; best dynamic single H=74.39 and dynamic repeat mean H=74.23 did not beat v4 confirmed H=74.45 or v5 repeat mean H=74.44. Version fit remains tied to direction/local/PSE routing points; ICSA full dynamic routing is recorded as a higher-risk variant rather than a default version action.",
+          "rationale": "TRIAL-001 已把 direction_sample h48 收敛成连续高分区域：ATTEMPT-017 最高单次 H=75.11，ATTEMPT-015 有 15 个 H>=74.80 job。ATTEMPT-018 对 75.11 候选做 5 次同配置同 seed exact repeat，最好 H=74.71、均值 H=74.58，未还原。因此该机制保留为有信号但不稳定的 trial，不进入 promotion。",
           "blockers": [
-            "ATTEMPT-001 did not exceed v4 confirmed_H=74.45 or v5 repeat mean H=74.44"
+            "ATTEMPT-018 未还原 ATTEMPT-017 的 H=75.11；最高重复 H=74.71、均值 H=74.58，promotion 继续 blocked"
           ]
         }
       },
       "base_versions": [
         "v5"
       ],
       "based_on_modules": [
         "PSE",
         "ICSA",
         "BVSA local_score",
         "BVSA direction mix",
         "FGVD",
         "SGMP"
       ],
       "target_component": "model/MyModel.py dynamic residual and score routing",
       "hypothesis": "Replacing v5 fixed coefficients with gates initialized near the fixed values can adapt local score strength, ICSA injection strength, BVSA direction mix, and PSE outer residual per sample or class. If the gates avoid collapse, they may preserve seen-class strength while improving unseen transfer and H stability.",
       "expected_effect": {
         "U": "Main target. Dynamic local/ICSA/PSE balance may improve unseen transfer by avoiding a single fixed seen-biased coefficient.",
         "S": "Should stay near v5 if gates initialize around v5 fixed values and anchor regularization is enabled.",
-        "H": "Target improvement is repeat mean above v5 repeat mean H=74.44 and preferably above v4 confirmed_H=74.45."
+        "H": "目标是让重复均值超过 v5 repeat mean H=74.44，并与 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47 比较。"
       },
       "implementation_scope": "TRIAL-001 only adds dynamic routing gates, config switches, gate statistics, tests, and two-GPU batch automation. The switch-off path must preserve v5 behavior. The trial does not change dataset split, class index order, evaluation metrics, optimizer, or promotion status.",
       "risk": "Gate collapse to 0/1, hidden seen-class overfit, sample/class broadcasting mistakes, silent switch-off drift, extra compute, and config alias drift are the main risks.",
       "compatibility": "use_dynamic_routing=false keeps the v5 fixed path. Fixed gate modes initialize to v5 values and provide an auditable bridge between static coefficients and learned gates.",
       "transfer_notes": "Treat as a routing mechanism tied to BVSA/PSE/ICSA. Reuse in later versions only after verifying class order, conditional text path, and score scale invariants.",
       "priority": 0.82,
       "linked_trials": [
         "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
       ],
       "linked_versions": [
         "v5"
       ],
@@ -275,23 +275,23 @@
           "type": "owner_hypothesis",
           "ref": "owner:2026-06-30",
           "note": "Owner proposed replacing residual-like coefficients a*x+(1-a)*x with dynamic routing gates."
         },
         {
           "type": "code_anchor",
           "ref": "model/MyModel.py",
           "note": "Existing fixed coefficients appear in PSE outer residual, ICSA text injection, BVSA direction mix, and final local_score blend."
         },
         {
           "type": "baseline_anchor",
           "ref": "experiments/v5/VERSION.md",
-          "note": "v5 is the active mainline; v4 confirmed_H=74.45 remains the confirmed reference."
+          "note": "v5 是 active mainline；正式 confirmed reference 是 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47。"
         },
         {
           "type": "trial",
           "ref": "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml",
-          "note": "ATTEMPT-017 H=75.11, delta_H=+0.57 vs v5 best_observed_H=74.54 (unconfirmed); trial decision=rerun."
+          "note": "ATTEMPT-017 最高单次 H=75.11；ATTEMPT-018 对该候选完成 5 次 exact repeat，best H=74.71、mean H=74.58，未还原且已到 hard cap；trial decision=revise，promotion blocked。"
         }
       ]
     }
   ]
 }
diff --git a/idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md b/idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
index 8acb25c..a2017ee 100644
--- a/idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
+++ b/idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
@@ -1,18 +1,18 @@
 # IDEA-0003: Dynamic Residual Routing

 ```text
 idea_id: IDEA-0003
 title: Dynamic Residual Routing
-status: selected
+status: weakened
 source_type: user
 source_ref: owner:2026-06-30:make residual and mixture coefficients dynamic routes
 source_status: local_heuristic
 global_score: 78.0
 idea_dir: idea_tree/ideas/IDEA-0003_dynamic_residual_routing/
 base_version: v5
 ```

 ## Source

 Owner hypothesis: several current GTPJ paths behave like fixed residual or mixture routes, for example `a*x + (1-a)*x` or `S_global + local_weight * S_local`.
 This idea tests whether those fixed coefficients should become learned dynamic gates rather than one global constant.
@@ -45,61 +45,59 @@ TRIAL-001 only adds:
 - Gate statistics in forward outputs and training logs.
 - Tests for shape, switch-off behavior, conditional BVSA text, and gradient reachability.
 - Workflow helpers for a balanced-aggressive 50-job two-GPU batch.

 TRIAL-001 must not change dataset split, class order, label mapping, logits shape, metric semantics, optimizer, or promotion status.

 ## Expected Effect

 | Metric | Expectation |
 |---|---|
 | U | Main target. Dynamic local/ICSA/PSE balance may improve unseen transfer by avoiding a single fixed seen-biased coefficient. |
 | S | Should stay near v5 if gates initialize around v5 fixed values and anchor regularization is enabled. |
-| H | Target improvement is repeat mean above v5 repeat mean H=74.44 and preferably above v4 confirmed_H=74.45. |
+| H | 目标是让重复均值超过 v5 repeat mean H=74.44，并与 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47 比较。 |

 ## Version Adaptation

 | Version | Score | Applicability | Stage | Rationale |
 |---|---:|---|---|---|
-| `v5` | 82.0 | direct | selected | v5 already routes `all_text_cond` into BVSA when configured, and has the fixed residual/mix coefficients this trial will replace dynamically. |
+| `v5` | 82.0 | direct | trialing | v5 already routes `all_text_cond` into BVSA when configured, and has the fixed residual/mix coefficients this trial will replace dynamically. |

 ## Compatibility

 - `use_dynamic_routing=false` keeps the v5 fixed path.
 - `dynamic_*_mode=fixed` initializes gates to the corresponding v5 scalar values.
 - New gates are trial-local until the result is promoted.

 ## Risks

 - Gate collapse to 0 or 1.
 - Hidden seen-class overfit.
 - Sample/class broadcasting mistakes.
 - Silent drift in switch-off behavior.
 - Config alias drift between framework names and legacy keys.
 - Extra compute or memory from class-wise gates.

 ## Decision Rule

 This idea can only move beyond trial evidence if:

 - 50-run batch has complete status and failure accounting.
 - Top2 frozen repeats complete.
-- Repeat mean clearly beats v5 repeat mean H=74.44 and is compared against v4 confirmed_H=74.45.
+- 重复均值明确超过 v5 repeat mean H=74.44，并与 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47 比较。
 - Interface and quality checks confirm class order, seen/unseen split, logits shape, and metric semantics are unchanged.

-## ATTEMPT-001 Result
+## 当前实验结果

-`TRIAL-001_dynamic-routing` ran `RUN-20260630-0005-dynroute50-2gpu` with 50 completed jobs and 0 failures.
+TRIAL-001 已记录到 ATTEMPT-018。当前研究前沿如下：

-Key evidence:
+- ATTEMPT-017 `DR-095 / a015dr035_weight_plus_0.01` 为最高单次，`H=75.11`、`U=73.00`、`S=77.36`、`ZS=82.12`。
+- ATTEMPT-015 的 100 jobs 中有 15 个 `H>=74.80`，其中 `75.04/75.00` 两个达到 75；ATTEMPT-011 也选出了 12 个 `H>=74.80` 来源候选。
+- ATTEMPT-018 对 `H=75.11` 候选完成 5 次同配置、同 seed exact repeat，最好 `H=74.71`、均值 `H=74.58`，未还原。
+- ATTEMPT-014 的 exact repeat 曾达到 `H=74.99`，但它还原的是来源目标 `74.89`，不能解释为 75 已复现。
+- 正式 confirmed reference 仍是 `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`。

-- best overall: DR-001 static control, H=74.40;
-- best dynamic single: DR-008 `local_class_h24`, H=74.39;
-- best direction single: DR-023 `direction_sample_h48_a0.003`, H=74.38;
-- best dynamic repeat mean: DR-008, H=74.23;
-- references: v4 confirmed H=74.45, v5 repeat mean H=74.44.
-
-Decision: no promotion. The idea remains selected for a revise/follow-up trial.
+结论：动态路由在 direction_sample h48 小 anchor 区域具有连续高分信号，但 75+ 来源候选尚未稳定复现。保留该 idea 为 `weakened/trialing`，`promotion_decision: blocked`。

 ## Next Action

-Run the `principled-followup` profile from `workflow/gtpj_workflow.py`: keep dynamic ICSA fixed, focus on direction/local/PSE gates, and repeat the top 3 candidates.
+不要继续追加 ATTEMPT-017 `DR-095` 的复现次数；它已经达到 5 次 hard cap。后续如继续研究，应基于 `74.8x/74.9x` 密集带提出新的机制假设或新候选，再走独立的 tune -> exact repeat 证据链。
diff --git a/idea_tree/queues/queue_state.yaml b/idea_tree/queues/queue_state.yaml
index 943b27c..7db8daa 100644
--- a/idea_tree/queues/queue_state.yaml
+++ b/idea_tree/queues/queue_state.yaml
@@ -1,34 +1,34 @@
 schema_version: "gtpj-queue-state/v1"
-updated_at: "2026-07-04"
+updated_at: "2026-07-11"
 current_window:
   focus: "GTPJ-v5 active mainline 后的近期复现、调参、队列整理和证据收尾。"
   policy: "只保留 3-7 条近期动作；完整创意库看 idea_tree/INDEX.md；具体实验动作写入 task/trial/attempt。"
 actions:
   - priority: "P0"
-    item: "每次正式 campaign 结束后执行 Warehouse checkpoint retention，只保留 Top-5 best model_best/best-model files 并记录 manifest。"
+    item: "每次正式 campaign 结束后执行 Warehouse checkpoint retention，只保留 Top-3 best model_best/best-model files 并记录 manifest。"
     type: "artifact_retention"
     owner: "Coordinator"
     status: "open"
     blocked_by: "-"
     evidence_ref: "docs/workflow/reference/artifact_policy.md"
   - priority: "P1"
     item: "继续 v5-based tuning 或 ablation，配置来源必须是 config/versions/v5.yaml。"
     type: "tune_or_ablation"
     owner: "Coordinator"
     status: "open"
     blocked_by: "需要 owner 指定调参、消融或混合实验范围。"
     evidence_ref: "experiments/v5/"
   - priority: "P1"
-    item: "下一轮调参后，用 repeat mean 判断 v5 是否超过 v4 confirmed_H=74.45。"
+    item: "下一轮调参后，用 repeat mean 判断 v5 是否超过 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47。"
     type: "confirmation_planning"
     owner: "Coordinator"
     status: "open"
     blocked_by: "需要先产生新的候选结果。"
     evidence_ref: "experiments/v5/confirmation/"
 completed:
   - item: "初始化 GTPJ repository 和 workflow helper。"
     evidence_ref: "docs/PROJECT_STRUCTURE.md"
   - item: "建立 GTPJ-v1 第一版正式 baseline，CUB seed=5 H=73.93。"
     evidence_ref: "experiments/v1/baseline/result.yaml"
   - item: "记录 GTPJ-v2 owner-activated，best_observed_H=74.29，confirmed_H pending。"
     evidence_ref: "experiments/v2/baseline/result.yaml"
diff --git a/idea_tree/versions/v5.md b/idea_tree/versions/v5.md
index 0a4cee1..b4321f7 100644
--- a/idea_tree/versions/v5.md
+++ b/idea_tree/versions/v5.md
@@ -1,16 +1,16 @@
 # v5 创意选择清单

 本文件只展示适用于 `v5` 的创意视图。总创意库见 `idea_tree/INDEX.md`。
 `idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。

 | 排名 | Idea | 标题 | Idea 文件 | 优先级 | 适用性 | 阶段 | 阻塞点 | 版本适配说明 |
 |---:|---|---|---|---:|---|---|---|---|
-| 1 | `IDEA-0003` | Dynamic Residual Routing | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | 82.0 | direct | trialing | ATTEMPT-001 did not exceed v4 confirmed_H=74.45 or v5 repeat mean H=74.44 | GTPJ-v5 already has fixed residual and mixture coefficients on the same active path: local_weight, icsa_ratio, weight_s2v, and pse_outer_ratio. TRIAL-001 ATTEMPT-001 completed 50/50 jobs; best dynamic single H=74.39 and dynamic repeat mean H=74.23 did not beat v4 confirmed H=74.45 or v5 repeat mean H=74.44. Version fit remains tied to direction/local/PSE routing points; ICSA full dynamic routing is recorded as a higher-risk variant rather than a default version action. |
+| 1 | `IDEA-0003` | Dynamic Residual Routing | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | 82.0 | direct | trialing | ATTEMPT-018 未还原 ATTEMPT-017 的 H=75.11；最高重复 H=74.71、均值 H=74.58，promotion 继续 blocked | TRIAL-001 已把 direction_sample h48 收敛成连续高分区域：ATTEMPT-017 最高单次 H=75.11，ATTEMPT-015 有 15 个 H>=74.80 job。ATTEMPT-018 对 75.11 候选做 5 次同配置同 seed exact repeat，最好 H=74.71、均值 H=74.58，未还原。因此该机制保留为有信号但不稳定的 trial，不进入 promotion。 |
 | 2 | `IDEA-0001` | CLIP-A-self text prototype adapter | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | 80 | direct | validated | - | Inherited by GTPJ-v5; v5 activates conditional BVSA text and tuned PSE/local weights but keeps the PSE interface and legacy aliases intact. |
-| 3 | `IDEA-0002` | FAE-memory JEPA auxiliary loss | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | 76 | direct | validated | - | TRIAL-003 extends IDEA-0002 by routing all_text_cond into BVSA cross/local_score. Owner activated the best main100 candidate as GTPJ-v5; v4 remains the stronger confirmed reference by repeat mean. |
+| 3 | `IDEA-0002` | FAE-memory JEPA auxiliary loss | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | 76 | direct | validated | - | TRIAL-003 通过把 all_text_cond 路由到 BVSA cross/local_score 扩展 IDEA-0002。Owner 已把 main100 最佳候选激活为 GTPJ-v5；更强的正式 confirmed reference 是 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47。 |

 ## 准入规则

 - 创新 trial 只能从本文件中 `阶段=selected` 且无阻塞点的 idea 启动。
 - `global_score` 只表示长期价值，不替代当前版本适配判断。
 - 新版本必须重新生成自己的 `versions/vX.md`，不能直接沿用旧版本清单。
diff --git a/workflow/README.md b/workflow/README.md
index 79651af..9079928 100644
--- a/workflow/README.md
+++ b/workflow/README.md
@@ -6,25 +6,25 @@

 ```text
 docs/GITHUB_GOVERNANCE.md
 docs/PROJECT_STRUCTURE.md
 docs/PROJECT_STATUS.md
 docs/workflow/reference/artifact_policy.md
 docs/workflow/reference/result_index_protocol.md
 docs/workflow/protocols/quality_gate.md
 docs/workflow/reference/agent_contracts.md
 ```

 当前 active mainline code 是 `GTPJ-v5 / tag v5`。`best_observed_H=74.54`，
-`confirmed_H=74.44`，仍需和更强 confirmed reference `v4 confirmed_H=74.45` 区分表述。
+`confirmed_H=74.44`，仍需和更强 confirmed reference `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47` 区分表述。当前 IDEA-0003/TRIAL-001 的研究最高单次为 `H=75.11`，但 exact repeat 未还原，不能写成 confirmed 或 promoted 结果。
 `validate` 会检查本地 baseline tag 是否能读到对应记录；`validate-remote`
 用于核对远端 `main` 和 baseline tags 是否与本地治理事实对齐。

 任何状态检查、结果比较、promotion 或 tag 前，先用只读命令判断复现状态：

 ```bash
 python workflow/gtpj_workflow.py repro-status --version v5
 ```

 如果输出 `verdict: needs_confirmation`，该版本只能作为 active code / unconfirmed reference，
 不能表述为 confirmed baseline。
```
