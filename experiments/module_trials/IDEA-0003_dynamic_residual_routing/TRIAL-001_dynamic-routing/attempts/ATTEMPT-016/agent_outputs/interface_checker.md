# Interface Checker

role_key: interface_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow
files_reviewed:
- task_start_card.md
- pre_run_plan.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml

summary: 本轮只复现 ATTEMPT-015 已存在的 dynamic routing 配置，不改变数据集、seen/unseen split、label mapping、class order、logits shape 或 U/S/H/ZS metric 语义。

