# ATTEMPT-018 Interface Checker

role_key: interface_checker
thread_title: ATTEMPT-018 | Interface Checker
decision: allow

## files_reviewed

- `AGENTS.md`
- `docs/workflow/START_HERE.md`
- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`
- `docs/workflow/agents/shared_roles/interface_checker/profile.md`
- `docs/workflow/reference/GZSL_HARD_RULES.md`
- `docs/workflow/reference/GENERAL_GZSL_EXPERIMENT_PROTOCOL.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/result.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/quality_check.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/task_start_card.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/pre_run_plan.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/quality_check.md`
- `workflow/gtpj_workflow.py`
- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `tools/helper_func.py`
- `tools/dataset.py`
- `config/versions/v5.yaml`

## interface_checks

- `exact_repeat` 边界：`ATTEMPT-017/result.yaml` 将 `DR-095` 记录为 `A017DR095`，源指标为 `H=75.11, U=73.00, S=77.36, ZS=82.12, best_epoch=48`，并声明下一步只能做同 seed、同配置的 `exact_repeat`；`ATTEMPT-018/task_start_card.md`、`pre_run_plan.md` 和 `manifest.yaml` 与此一致，锁定 `original_seed: 5`、`restore_target_H: 75.11`、`max_attempts: 5`、`early_stop_on_best_hit: true`、`seed_change_allowed: false`。
- A017DR095 profile：`workflow/gtpj_workflow.py` 中 `confirmation_policy_for_profile()` 将 `h76-a017dr095-restore5-exact-repeat` 归入 `exact_repeat`，并设置 `formal_confirmation_evidence: true`、`original_seed: 5`、`max_attempts_hard_cap: true`、`seed_change_allowed: false`；`_h76_a017dr095_restore5_exact_repeat_specs()` 只生成 5 个同一候选的 repeat job，均携带 `source_candidate_id=A017DR095`、`source_job_id=DR-095`、`source_H=75.11`、`restore_target_H=75.11`。
- 配置漂移：A017DR095 的 planned updates 与 ATTEMPT-017 源候选一致：`use_dynamic_routing: true`、`dynamic_local_mode: fixed`、`dynamic_icsa_mode: fixed`、`dynamic_direction_mode: sample`、`dynamic_pse_mode: fixed`、`dynamic_gate_hidden: 48`、`dynamic_gate_anchor_lambda: 0.0035`、`weight_s2v: 0.535`、`random_seed: 5`。未发现修改 dataset、split、class order、batch size、epoch schedule、evaluation path 或 label mapping 的 planned update。
- 动态 routing 支持模式：helper 默认 `_dynamic_updates()` 只打开已登记的 dynamic routing 开关；本 profile 使用 `dynamic_pse_mode=fixed`，没有使用被禁止的 `dynamic_pse_mode=sample`。`build_dynamic_routing_jobs()` 对 `dynamic_pse_mode` 做保护，只允许 `None/fixed/class`；`model/MyModel.py` 也在模型初始化阶段拒绝 `dynamic_pse_mode` 之外的值。
- seen/unseen split 与 class order：`tools/dataset.py` 继续从 xlsa17 的 `att_splits.mat` 读取 `trainval_loc`、`test_seen_loc`、`test_unseen_loc`，并由全局标签生成 `seenclasses` 与 `unseenclasses`；A017DR095 profile 没有触碰数据读取、split 文件或类别顺序。
- label mapping：`train_GTPJ_CUB.py` 仍按 `dataloader.seenclasses` 和 `dataloader.unseenclasses` 切分文本原型；`model/MyModel.py` 在训练 loss 中通过 `_global_to_seen_labels()` 将全局 seen label 映射到 seen 局部编号，并在遇到 unseen label 时抛错。该映射属于训练内部映射，未替代评估全局标签。
- logits shape：`model/MyModel.py` 的接口注释和 forward 逻辑一致：`is_train=True` 输出 `[B（图片/样本数量）, n_seen（seen 类数量）]`；`is_train=False` 输出 `[B（图片/样本数量）, num_class（全类别数量）]`，并保留 `logits_200/s_final`。A017DR095 只调 routing gate 与 `weight_s2v`，未改变 logits 轴或输出字段。
- metric semantics：`train_GTPJ_CUB.py` 仍调用 `tools.helper_func.eval_zs_gzsl()`；该函数在 `test_seen_loader` 和 `test_unseen_loader` 上分别计算 seen/unseen 准确率，`GZSL-H` 仍为 `2 * acc_seen * acc_novel / (acc_seen + acc_novel)`，`ZSL` 仍是 unseen-only candidate labels 下的指标。`workflow/gtpj_workflow.py` 的 batch parser 只从训练日志的 `GZSL-U/S/H` 与 `ZSL` 字段抽取结果，没有改写指标定义。
- stop policy：`maybe_stop_after_confirmation_hit()` 只在单次 repeat 达到 `restore_target_H` 后跳过同候选剩余 repeat；若落入 tolerance 但低于目标，只记录 `near_miss_not_restored` 并继续。该行为符合 ATTEMPT-018 对 exact repeat 的恢复判定。

## blocking_issues

- 无。按已读文件和相关代码，A017DR095 exact repeat 的 GZSL 接口、label mapping、seen/unseen split、class order、logits shape、metric semantics 和动态 routing 支持模式没有发现不清楚或漂移到不支持组合的问题。

## non_blocking_warnings

- 当前工作区存在大量既有 dirty / untracked 文件，包括 workflow 文档、`workflow/gtpj_workflow.py`、ATTEMPT-017/018 目录等。本报告只判定接口不阻塞；是否允许正式 Runner 仍需 Reviewer、Runner Monitor、Evidence Quality Checker、`agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight` 和计划中列出的机器 gate 独立通过。
- `ATTEMPT-018/agent_summary.md` 当前仍写着 `verified_against_current_repo: pending`，说明本角色报告写入后还需要 Coordinator 汇总更新正式 gate 状态。
- 本次没有生成 `.gtpj_runtime` batch、没有启动 Runner，也没有检查服务器实际 GPU、screen、run directory 可用性；这些属于 Runner Monitor 范围。

## uncovered_scope

- 未审查 Reviewer 对 helper profile/test 的独立结论。
- 未审查 Runner Monitor 对服务器资源、目标目录污染、GPU 锁和启动命令的结论。
- 未审查 Evidence Quality Checker 对 ATTEMPT-017 源证据和 ATTEMPT-018 账本完整性的结论。
- 未运行训练、未读取 ATTEMPT-018 未来 run 输出、未判断 restored/near-miss/stability 结果。
- 未执行 `validate-agent-runtime`、`multi-agent-preflight`、`validate`、`audit-boundary`、`validate-evidence-routing` 或 `git diff --check`；这些是正式 Runner 前仍需完成的外部门禁。
