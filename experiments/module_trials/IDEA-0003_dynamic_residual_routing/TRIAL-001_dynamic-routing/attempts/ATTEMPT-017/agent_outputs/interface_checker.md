# Interface Checker

role_key: interface_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow

files_reviewed:
- task_start_card.md
- pre_run_plan.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml
- model/MyModel.py
- train_GTPJ_CUB.py
- workflow/gtpj_workflow.py

summary: 本轮只使用现有配置开关：`dynamic_direction_mode`、`dynamic_gate_hidden`、`dynamic_gate_anchor_lambda`、`weight_s2v`、`dynamic_local_mode`、`local_weight`、`dynamic_pse_mode=class`、`pse_outer_ratio`、`dynamic_icsa_mode`、`icsa_ratio`。不改变数据集、seen/unseen split、label mapping、class order、logits shape 或 U/S/H/ZS metric 语义。`dynamic_pse_mode=sample` 不会生成。
