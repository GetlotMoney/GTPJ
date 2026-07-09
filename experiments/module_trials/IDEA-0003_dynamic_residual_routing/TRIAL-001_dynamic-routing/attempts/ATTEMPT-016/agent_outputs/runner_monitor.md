# Runner Monitor

role_key: runner_monitor
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow
files_reviewed:
- task_start_card.md
- pre_run_plan.md
- WORK_ITEMS.md
- workflow/gtpj_workflow.py

summary: 允许生成本地 frozen plan。服务器上传和启动前仍需只读确认 lab4090 commit、GPU、同 run id 进程和目标目录状态。

