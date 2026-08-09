# ATTEMPT-013 Interface Checker Output

role: interface_checker

agent_instance_id: 019f3bed-b90e-7371-9ee6-e90be971de80

files_reviewed:

- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`
- `docs/workflow/reference/GZSL_HARD_RULES.md`
- `docs/workflow/protocols/module_trial_protocol.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/task_start_card.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/pre_run_plan.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/WORK_ITEMS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/agent_runtime.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/quality_check.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/result.yaml`
- `workflow/gtpj_workflow.py`
- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `tools/helper_func.py`
- `tools/dataset.py`

decision: allow

uncovered_scope:

- 未检查服务器 frozen batch、`plan.json`、job-level runtime config、summary、checkpoint 或 artifact hash，因为 ATTEMPT-013 当前声明为 planning only，Runner 尚未启动，batch 目录尚未创建。
- 未检查 lab4090 commit/GPU/进程/STOP_REQUESTED 运行态，因为本次委托禁止启动服务器和训练。
- 未重新验证 ATTEMPT-011/012 原始日志；它们在本轮仅作为候选来源和弱先验，不作为 ATTEMPT-013 的正式结果证据。

interface_semantics_changed: no

required_next_action:

若 owner 后续要求真实运行，Runner 启动前必须先生成 frozen batch plan 和 per-job configs，再由 Interface Checker 复核实际 `plan.json` / runtime configs 是否仍只覆盖 `use_dynamic_routing`、`dynamic_direction_mode=sample`、`dynamic_gate_hidden=48`、`dynamic_gate_anchor_lambda`、`weight_s2v`、`random_seed`，并确认 local/server commit 对齐、agent runtime gate 通过、STOP_REQUESTED 机制存在。

## 检查结论

本轮 ATTEMPT-013 可允许继续本地 planning gate；不允许把本结论解释为可以立即启动服务器 Runner。计划语义清楚：5 个 `direction_sample h48` 小 anchor 候选，各跑 seeds 6-15，共 50 jobs，用于多 seed 稳定性检查。

未发现 ATTEMPT-013 计划改变 label mapping、seen/unseen split、class order、logits shape、metric semantics 或 GZSL 评估语义。

## 关键依据

- `pre_run_plan.md`、`WORK_ITEMS.md`、`manifest.yaml` 和 `ATTEMPTS.md` 一致声明 5 个候选：DR047、DR020、DR041、A011DR042、A011DR020；参数只涉及 `dynamic_direction_mode=sample`、`h=48`、`weight_s2v`、`anchor_lambda` 和 seeds 6-15。
- `workflow/gtpj_workflow.py` 中 `H76_FOLLOWUP50_MULTI_SEED_CANDIDATES` 与 `_h76_followup50_multiseed_specs()` 只展开上述 5x10 jobs；`_dynamic_updates()` 的默认值保持 `dynamic_local_mode=fixed`、`dynamic_icsa_mode=fixed`、`dynamic_pse_mode=fixed`，本 profile 只覆写 direction gate、hidden、anchor、`weight_s2v` 和 `random_seed`。
- Trial `config.yaml` 的数据集仍是 CUB，`num_class=200`；ATTEMPT-013 文件未声明修改数据路径、split 文件、class order 或 label mapping。
- `model/MyModel.py` 的接口契约仍是 train logits `[B（图片/样本数量）, n_seen（seen 类数量）]`，eval logits `[B（图片/样本数量）, num_class（全部类别数量）]`；forward 中训练态仍切 seen 列，评估态仍输出全类 `s_final`。
- `tools/dataset.py` 仍从 `att_splits.mat` 读取 `trainval_loc`、`test_seen_loc`、`test_unseen_loc`，并由这些位置派生 seen/unseen 类集合。
- `tools/helper_func.py` / `train_GTPJ_CUB.py` 仍用 `eval_zs_gzsl()` 计算 GZSL-U、GZSL-S、GZSL-H 和 ZSL；H 仍是 U/S 调和平均。

## 语义判定

- label mapping: unchanged by plan
- seen/unseen split: unchanged by plan
- class order: unchanged by plan
- logits shape: unchanged by plan
- metric semantics: unchanged GZSL U/S/H/ZS by protected evaluator
- GZSL evaluation semantics: unchanged
- ATTEMPT-012 partial: weak prior only, not merged into ATTEMPT-013 result evidence
