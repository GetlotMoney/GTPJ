# Evidence Quality Checker

role_key: evidence_quality_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow
files_reviewed:
- task_start_card.md
- pre_run_plan.md
- WORK_ITEMS.md
- tests/test_gtpj_workflow.py

summary: 复现规则正确：seed 固定为 5，每候选最多 5 次，只有达到 `restore_target_H` 才算 restored；near miss 只能记录希望，不能 confirmation 或 promotion。

