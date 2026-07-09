# ATTEMPT-014 Quality Check

## 当前状态

当前是 pre-run planning。尚未上传，尚未启动服务器 Runner，尚无结果。

## 已检查

- 候选来源来自 ATTEMPT-011 完成后的服务器 summary 回写。
- ATTEMPT-013 被排除，因为它换 seed，不是 exact repeat。
- 本轮复现规则固定为原 seed=5、原配置、每候选最多 5 次。
- near miss 只标记 `near_miss_not_restored`，不能作为 restoration。
- 本地 frozen plan 已生成：100 jobs、20 个 source candidates、每个 5 jobs。
- 所有 jobs 的 `seed` 和 `config_updates.random_seed` 均为 5。
- 每个 job 都带 `restore_target_H`，`confirmation_policy.per_job_restore_target_H=true`。

## 启动前必须检查

- `plan.json` 中必须有 100 jobs。
- 必须正好 20 个 `source_candidate_id`，每个 5 jobs。
- 所有 jobs 的 `seed` 和 `config_updates.random_seed` 必须是 5。
- 每个 job 必须有自己的 `restore_target_H`。
- `confirmation_policy.per_job_restore_target_H` 必须为 true。
- 服务器预检必须确认 GPU 空闲、同 run id 无旧进程、目标目录未污染。

## 服务器只读预检

- lab4090 branch: `codex/workflow-closeout-speed-fixes`
- lab4090 HEAD: `a884fea`
- target run dir: missing
- same run id process: none
- GPU0/GPU1: idle, memory used 6 MiB each, utilization 0%
- target worktrees `dynroute_a884fea_gpu0/gpu1`: missing; runner will create them from commit.
- note: server main repo has unrelated dirty workflow/test files and temp files; formal run must rely on commit worktrees plus uploaded frozen batch, not the dirty main worktree.

## Gate

- formal_result_evidence_exists: false
- runner_started: false
- local_frozen_plan_generated: true
- server_readonly_preflight_done: true
- promotion_decision: blocked

## 2026-07-08 启动更新

- `RUN-20260708-0001-h76-restore100-exact-repeat-2gpu` 已判定为 runner 环境失败：计划记录的是本地 commit/branch，服务器仓库无法解析，100 个 job 都在训练前失败；不作为方法证据、复现证据或结果证据。
- 已重新生成并上传 `RUN-20260708-0002-h76-restore100-exact-repeat-2gpu`。
- 新计划固定服务器 HEAD：`d505e992492eb6fe7272edf0f0dc1d15a5932434`，并设置 `git_remote=none`，避免服务器启动时抓取本地不存在的分支。
- 服务器端结构校验通过：100 configs、100 jobs、20 个 source candidates、每个候选最多 5 次 exact repeat、所有 job 的 seed 都是 5、`confirmation_policy.per_job_restore_target_H=true`。
- 服务器端哈希校验通过：
  - `plan.json`: `83fff0f488d96940f9ad8039e4ef2e5426db2f8fbf3fcbde1b97595433884abf`
  - `batch_status.json`: `549f4cf670c5365bf59e32b70b81365ff3e44d1cee86dcaba1cea2098280cd39`
  - `run_dynamic_routing_batch.py`: `609bcee227ede155861f19809e254b1d36ade6b034fca36e5bb377e587920eaf`
  - `start_batch.sh`: `23364bfc4939e109321f1b6dbe980abb6cd61f4fba1ab1bb7938cbc3583a6316`
- 已用 `screen -dmS GTPJ_ATTEMPT014_RESTORE100_R2` 启动 detached runner。
- 启动后只读确认：`screen` 存在，两个 controller PID 存在，两个 `train_GTPJ_CUB.py` 进程已分别启动，`batch_status.json` 显示 `running: 2, pending: 98`。
- promotion 仍然 blocked；必须等 exact-repeat 结果和质量检查完成后再讨论。

## Post-Run Quality Check

- 有效运行：`RUN-20260708-0002-h76-restore100-exact-repeat-2gpu`。
- 旧运行 `RUN-20260708-0001-h76-restore100-exact-repeat-2gpu` 是 commit mismatch 导致的训练前环境失败，不进入方法证据。
- 运行完成状态：80 completed / 20 skipped / 0 failed。
- skipped 的原因是同一 source candidate 已经有 repeat 达到该候选自己的 `restore_target_H`，触发 `early_stop_on_best_hit` 后跳过剩余 repeat；这是 ATTEMPT-014 policy 允许的行为。
- 没有任何完成 job 达到 H>=75。
- 两个 source_H=75.00 的候选都没有还原：
  - `A011B01DR042`: best H=74.81, mean H=74.690。
  - `A011B04DR036`: best H=74.80, mean H=74.684。
- 本轮只支持 `tune_promising`，不能写成 `confirmed`、`stable_confirmed`、`promotion_candidate` 或 baseline-grade evidence。
- GZSL 指标语义未变；本轮只调已有 dynamic routing config 参数，不改变代码接口、label mapping、seen/unseen split、class order 或 metric 计算。
- promotion 继续 blocked。
