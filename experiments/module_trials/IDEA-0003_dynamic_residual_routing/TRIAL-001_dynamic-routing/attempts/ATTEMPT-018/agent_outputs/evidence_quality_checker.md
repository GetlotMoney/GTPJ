role_key: evidence_quality_checker
thread_title: ATTEMPT-018 | Evidence Quality Checker
decision: allow

# recheck_summary

本次只读 recheck 结论为 `allow`。ATTEMPT-017 的 `DR-095 / A017DR095` 证据足以派生 ATTEMPT-018 的 exact repeat，但仍只属于 `valid_single_run -> exact_repeat candidate`，不能直接升级为 confirmed、stable_confirm 或 promotion evidence。

Evidence Quality 范围内，Coordinator 已补齐上次 block 的关键项：`ATTEMPTS.md` formal pending 行、`agent_runtime.yaml` 真实左侧命名线程 ID、`TRANSITIONS.jsonl`、`evidence_routing.yaml`、以及 source actual training commit 与 local plan generation commit 的分离记录。若 Runner Monitor recheck 也给出 `allow`，可以允许 Coordinator 将 `agent_runtime.yaml` 升级为全 allow，并在 `validate-agent-runtime` 与 `multi-agent-preflight` 通过后生成/上传/启动 `live_multi_agent_monitor` run。

# files_reviewed

- `AGENTS.md`
- `docs/workflow/START_HERE.md`
- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`
- `docs/workflow/agents/shared_roles/quality_checker/profile.md`
- `docs/workflow/playbooks/confirmation.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/result.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/evidence_routing.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/TRANSITIONS.jsonl`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/quality_check.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/task_start_card.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/pre_run_plan.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/quality_check.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/WORK_ITEMS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/AGENT_ACTIVITY.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_summary.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_runtime.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/TRANSITIONS.jsonl`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/evidence_routing.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/reviewer.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/runner_monitor.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/interface_checker.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/log_analyst.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/result_analyst.md`
- `workflow/gtpj_workflow.py` 中 `validate-evidence-routing`、`validate-agent-runtime`、`multi-agent-preflight` 对应 helper 行为

# evidence_checks

- `ATTEMPT-017 source evidence`: pass。`result.yaml` 记录 `completed_jobs: 100`、`failed_jobs: 0`、`skipped_jobs: 0`，`DR-095` 为 best single，指标为 `H=75.11, U=73.00, S=77.36, ZS=82.12, best_epoch=48`。同文件明确 `evidence_level: valid_single_run`、`confirmation_decision: not_confirmation_evidence`、`promotion_decision: blocked`。
- `ATTEMPT-017 transition/routing`: pass。`evidence_routing.yaml` 指向 `ER-20260709-ATTEMPT017-002`，状态为 `tune_promising`；`TRANSITIONS.jsonl` 记录 `EXACT_REPEAT.REQUIRED_FOR_DR095` 与 `PROMOTION.BLOCKED` 均为 pass。
- `exact repeat derivation`: pass。ATTEMPT-018 的 `task_start_card.md`、`pre_run_plan.md`、`manifest.yaml` 均继承 `A017DR095 / DR-095`、`repeat_type: exact_repeat`、`original_seed: 5`、`restore_target_H: 75.11`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`near_miss_not_restored: true`、`seed_change_allowed: false`。
- `config boundary`: pass。ATTEMPT-018 固定配置与 ATTEMPT-017 `exact_repeat_candidate.config_updates` 一致：`use_dynamic_routing: true`、`dynamic_local_mode: fixed`、`dynamic_icsa_mode: fixed`、`dynamic_direction_mode: sample`、`dynamic_pse_mode: fixed`、`dynamic_gate_hidden: 48`、`dynamic_gate_anchor_lambda: 0.0035`、`weight_s2v: 0.535`、`random_seed: 5`。未发现 Evidence Quality 范围内的 seed/config 边界漂移。
- `ledger sufficiency`: pass。`ATTEMPTS.md` 已新增 `ATTEMPT-018` 行，run id 为 `RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu`，状态为 `pre_run_gated`，best dynamic 为 `A017DR095 / DR-095 exact-repeat restore candidate`，repeat evidence 写明 `max 5 same-seed exact repeats, stop on H>=75.11; near miss remains not restored`，decision 写明 `formal_pending; live_multi_agent_monitor gate must pass before runner start`。
- `runtime gate material`: pass_with_pending_update。`agent_runtime.yaml` 已记录六个真实左侧命名线程 ID、准确标题、状态引用、输出引用、`live_multi_agent_monitor`/`named_owner_thread`/`left_sidebar_named_threads` 语义。当前文件仍保留 `runner_monitor: block`、`evidence_quality_checker: block`、`pre_run_allow_checks_passed: false`、`agent_runtime_validated: false`，这是旧 recheck 状态，不构成本角色继续 block；Coordinator 应在 Runner Monitor 也 allow 后更新这些字段并重跑 gate。
- `transition/evidence routing material`: pass。ATTEMPT-018 已有 `TRANSITIONS.jsonl` 与 `evidence_routing.yaml`；当前 routing 状态为 `blocked`，链头为 `ER-20260709-ATTEMPT018-001`，其 block 原因正是等待 Runner Monitor 与 Evidence Quality recheck。`validate-evidence-routing` 当前通过，说明 transition/routing 结构足够。
- `commit pin separation`: pass。`manifest.yaml` 与 `pre_run_plan.md` 均明确 source actual training commit / planned training commit 为 `d505e992492eb6fe7272edf0f0dc1d15a5932434`，local ledger/helper plan generation commit 为 `a884fea429a302fecc42ba8cddf9e6e66f5d07c8`。这足以区分 ATTEMPT-017 实际训练代码与 ATTEMPT-018 本地计划生成代码。
- `artifact boundary`: pass_for_pre_run。ATTEMPT-017 manifest 对 summary、events、batch status、server status、plan 等 artifact 均有 artifact id、URI、sha256、size 与 status；ATTEMPT-018 尚未运行，仅声明 Warehouse scope 与目标 run path，没有把未来 raw logs/checkpoints/results 写成已存在证据。
- `role-output consistency`: pass_with_known_stale_text。Reviewer、Interface Checker、Log Analyst、Result Analyst 已为 allow；Runner Monitor 与旧 Evidence Quality 输出中关于“缺少 agent_runtime / ledger / routing / commit pin”的文字已经被 Coordinator 后续补齐。Runner Monitor 仍需独立 recheck；Evidence Quality 本文件覆盖后不再阻断。
- `runner-start permission`: conditional_allow。Evidence Quality 允许 Coordinator 在 Runner Monitor 也 allow 后升级 `agent_runtime.yaml` 为全 allow，并生成/上传/启动 `live_multi_agent_monitor` run；但本文件本身不是 Runner 启动令，不能绕过 Runner Monitor、`validate-agent-runtime`、`multi-agent-preflight` 或服务器资源预检。

# blocking_issues

- 无 Evidence Quality 范围内的剩余阻断项。

# non_blocking_warnings

- 当前 `agent_runtime.yaml` 仍记录旧状态：Runner Monitor 与 Evidence Quality 为 `block`，`pre_run_allow_checks_passed: false`，`agent_runtime_validated: false`。本报告只解除 Evidence Quality 的 block；Coordinator 必须等 Runner Monitor 同步 allow 后再更新 runtime，并重跑 `validate-agent-runtime` 与 `multi-agent-preflight`。
- `validate-agent-runtime` 与 `multi-agent-preflight` 在当前旧 runtime 上失败，失败原因正是 `runner_monitor`/`evidence_quality_checker` 仍非 allow 以及 preflight 标志未更新；这是预期的 pending-update 状态，不应被误读为 ATTEMPT-017 evidence 不足。
- `ATTEMPT-018/agent_summary.md`、`quality_check.md`、`WORK_ITEMS.md` 当前仍描述 `pre_run_blocked_pending_recheck`；Coordinator 在收齐 Runner Monitor 与 Evidence Quality 新 allow 后需要同步这些 ledger 状态。
- 工作区存在大量既有 modified/untracked 文件，且本 recheck 没有做 clean freeze、远端同步、server GPU 预检或 run-dir collision 复核；这些属于 Coordinator / Runner Monitor 启动前职责。
- ATTEMPT-018 即使命中 `H >= 75.11`，也只能回答“DR-095 best single 是否原样 restored”；除非另有稳定性 repeat mean/min/max/range 证据与质量门，否则不能直接写 promotion-facing confirmed mean 或论文 claim。

# uncovered_scope

- 未启动训练、未生成 `.gtpj_runtime` batch、未上传服务器、未启动 screen、未 push/delete/tag。
- 未连接 lab4090 重新计算 ATTEMPT-017 artifact sha256，也未读取远端 raw logs / checkpoints / screen / GPU 实时状态。
- 未复核 Runner Monitor 的资源层结论；Runner Monitor 必须独立更新为 `allow` 后，Coordinator 才能升级 runtime。
- 未检查 ATTEMPT-018 未来 `result.yaml`、Warehouse artifacts、batch status、events、completed job metrics 或 checkpoint retention，因为本轮尚未运行。
- 未作 promotion、version tag、baseline claim 或论文 claim 决策。

# validation_run

- `python workflow\gtpj_workflow.py validate-evidence-routing` -> `validate-evidence-routing-ok subjects=13`
- `python workflow\gtpj_workflow.py validate` -> `validate-ok`
- `python workflow\gtpj_workflow.py validate-workflow-consistency` -> `validate-workflow-consistency-ok`
- `python workflow\gtpj_workflow.py audit-boundary` -> `audit-boundary-ok`
- `python workflow\gtpj_workflow.py validate-agent-runtime --path experiments\module_trials\IDEA-0003_dynamic_residual_routing\TRIAL-001_dynamic-routing\attempts\ATTEMPT-018\agent_runtime.yaml` -> 当前失败，原因仅为 runtime 仍记录 `runner_monitor` 与 `evidence_quality_checker` 非 allow，以及 preflight 标志未更新。
- `python workflow\gtpj_workflow.py multi-agent-preflight --path experiments\module_trials\IDEA-0003_dynamic_residual_routing\TRIAL-001_dynamic-routing\attempts\ATTEMPT-018\agent_runtime.yaml` -> 当前失败，原因同上；Runner Monitor allow 与 Coordinator runtime 升级后必须重跑并通过。

# verdict

Evidence Quality verdict: `allow`。可以让 Coordinator 在 Runner Monitor 也 `allow` 后将 `agent_runtime.yaml` 升级为全 allow，并在 `validate-agent-runtime` 与 `multi-agent-preflight` 通过后进入 `live_multi_agent_monitor` 生成/上传/启动流程。
