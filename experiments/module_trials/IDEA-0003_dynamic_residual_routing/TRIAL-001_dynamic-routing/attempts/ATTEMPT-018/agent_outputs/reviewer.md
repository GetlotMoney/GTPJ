role_key: reviewer
thread_title: ATTEMPT-018 | Reviewer
decision: allow

# 审核结论

本 Reviewer 结论为 `allow`：新增 `h76-a017dr095-restore5-exact-repeat` helper profile 与当前相关测试，足以支持后续生成 DR-095 的 exact repeat formal plan。该结论只覆盖 helper profile、计划生成逻辑和测试覆盖，不等同于允许启动 Runner。

# files_reviewed

- `AGENTS.md`
- `docs/workflow/START_HERE.md`
- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`
- `docs/workflow/protocols/ai_cross_review_protocol.md`
- `docs/workflow/playbooks/confirmation.md`
- `docs/workflow/agents/shared_roles/reviewer/profile.md`
- `docs/workflow/agents/by_experiment/confirmation/agents/README.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/task_start_card.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/pre_run_plan.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/WORK_ITEMS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/AGENT_ACTIVITY.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/interface_checker.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_outputs/result_analyst.md`
- `workflow/gtpj_workflow.py` 中 A017DR095 profile、confirmation policy、batch plan 与 stop policy 相关代码
- `tests/test_gtpj_workflow.py` 中 A017DR095 profile 与 exact repeat policy 相关测试

# blocking_issues

- 无。实现中 `confirmation_policy_for_profile()` 已将 `h76-a017dr095-restore5-exact-repeat` 归入 `exact_repeat`，并设置 `formal_confirmation_evidence: true`、`original_seed: 5`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`per_job_restore_target_H: true`、`seed_change_allowed: false`。
- 无。`_h76_a017dr095_restore5_exact_repeat_specs()` 只生成 5 个 `A017DR095 / DR-095` 同配置、同 seed repeat job，携带 `source_run_id=RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu`、`source_job_id=DR-095`、`source_H=75.11` 和 `restore_target_H=75.11`。
- 无。`cmd_plan_dynamic_routing_batch()` 会在 formal 模式下要求 `--agent-runtime-gate`，校验 profile job count 与 `--jobs` 一致，并把 confirmation policy 与 jobs 写入 `plan.json`；这能防止 `--jobs 5` 以外的误生成。
- 无。runner stop policy 对 exact repeat 命中使用 `H >= restore_target_H`，命中后跳过同候选剩余 repeat；near miss 只记录 `near_miss_not_restored` 并继续，不会被误判为 restored。

# non_blocking_warnings

- 当前没有生成 `.gtpj_runtime/batches/RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu/plan.json`；我只做只读审核和测试验证，未调用会写 runtime batch 的 plan 命令。
- 当前 `ATTEMPT-018/agent_runtime.yaml` 不存在；因此正式 plan 生成和 Runner 启动仍必须等待 Coordinator 写入真实命名线程 gate，并通过 `validate-agent-runtime` 与 `multi-agent-preflight`。
- `tests/test_gtpj_workflow.py` 已覆盖 A017DR095 的 builder 与 confirmation policy；现有 CLI plan 写入逻辑由其他 exact-repeat plan 测试覆盖。建议后续可补一个 A017DR095 专属 `plan-dynamic-routing-batch --jobs 5` 回归测试，但这不是本轮阻断项。
- `ATTEMPTS.md` 当前可见 ATTEMPT-017 将 DR-095 标为 exact_repeat next；我未把 formal ledger 完整性作为本 Reviewer 的放行范围，需由 Evidence Quality Checker 或 Coordinator 最终确认 ATTEMPT-018 待跑账本状态。
- 当前工作区已有大量既有 dirty / untracked 文件。本报告不回滚、不整理这些文件，只评价 A017DR095 helper profile 和相关测试。

# uncovered_scope

- 未启动 Runner，未创建 batch，未写 `.gtpj_runtime`，未检查服务器 GPU、screen、远端 run directory、GPU lock 或实际 stop 文件机制。
- 未执行 `validate-agent-runtime` 或 `multi-agent-preflight`，因为当前 `ATTEMPT-018/agent_runtime.yaml` 尚不存在。
- 未判定 ATTEMPT-017 源证据、Warehouse artifact、日志 hash、checkpoint retention 或 ATTEMPT-018 formal ledger 是否足够；这些属于 Evidence Quality Checker / Runner Monitor / Coordinator 范围。
- 未判定未来结果是否 restored、near_miss_not_restored、not_restored、stable_confirm 或 promotion-facing evidence；本轮只审核预跑 helper 和测试。
- 未审查与 A017DR095 无关的 dynamic routing profiles、训练入口、模型 forward、数据 split 或 metric 实现改动。

# validation_run

- `git status --short --branch`：当前分支 `codex/attempt017-server-frozen-escape100`，工作区存在大量既有 modified / untracked 文件；未回滚。
- `Test-Path ATTEMPT-018/agent_runtime.yaml`：`False`。
- `Test-Path .gtpj_runtime/batches/RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu`：不存在，未生成 runtime plan。
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_gtpj_workflow.WorkflowHelperTest.test_dynamic_routing_batch_plan_has_a017dr095_restore5_jobs tests.test_gtpj_workflow.WorkflowHelperTest.test_dynamic_routing_a017dr095_restore_policy_uses_per_job_restore_target`：通过，2 个测试 OK。
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_gtpj_workflow`：通过，158 个测试 OK。
- `python workflow\gtpj_workflow.py validate`：`validate-ok`。
- `python workflow\gtpj_workflow.py validate-workflow-consistency`：`validate-workflow-consistency-ok`。
- `python workflow\gtpj_workflow.py audit-boundary`：`audit-boundary-ok`。
- `git diff --check -- workflow/gtpj_workflow.py tests/test_gtpj_workflow.py experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018`：通过，无输出。
