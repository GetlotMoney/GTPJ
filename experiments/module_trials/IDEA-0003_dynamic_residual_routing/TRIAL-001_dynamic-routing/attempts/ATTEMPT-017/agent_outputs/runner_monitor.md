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
- lab4090 screen/GPU/process read-only snapshot

summary: 允许生成 frozen plan，并允许服务器 detached supervisor 排队启动。由于 ATTEMPT-016 仍在运行，本轮 supervisor 必须先等待无 `run_dynamic_routing_batch.py` / `train_GTPJ_CUB.py` 进程、GPU 空闲、目标 run 目录未污染，再执行 `start_batch.sh`。
