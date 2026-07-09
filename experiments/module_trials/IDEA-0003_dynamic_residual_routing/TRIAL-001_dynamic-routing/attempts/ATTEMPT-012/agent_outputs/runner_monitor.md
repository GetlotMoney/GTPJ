# Runner Monitor

role_key: runner_monitor
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
status: allow

检查结论：本轮可以进入服务器 detached 启动前预检。要求启动前确认 lab4090 GPU 空闲、目标 run 目录不存在活跃进程污染、batch plan 已冻结并上传。停止机制使用 batch 目录内的 `STOP_REQUESTED` 文件。
