# Runner 监控检查

role_key: runner_monitor
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow

files_reviewed:
- TASK_START.yaml
- PARAMETER_MATRIX.csv
- DATA_MANIFEST.json
- tools/run_v5_ablation_001_server_controller.py
- tests/test_v5_ablation_server_linux_integration.py

检查结论：允许在 strict-3 审核、运行时校验和冻结提交全部通过后启动服务器控制器。控制器必须先确认 GPU 0、1 无计算进程，再按 FULL 与 GLOBAL_ONLY 两个固定队列运行。停止只通过运行目录里的 `STOP` 文件或控制器信号处理；半截运行不得复用旧目录、旧提交或旧 `run_id`。
