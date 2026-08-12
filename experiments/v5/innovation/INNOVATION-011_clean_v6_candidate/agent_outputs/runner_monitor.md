# Runner Monitor 开跑检查

```text
role_key: runner_monitor
decision: allow
```

- `lab4090` 的 `dvsr_gpu` Python 可执行文件存在。
- GPU 0 当前没有训练进程；只给本次运行暴露 GPU 0。
- Warehouse 的 `V5-INNOVATION-011/RUN-001` 目录当前不存在，不会覆盖历史结果。
- 服务器旧主仓有本地改动，因此本次只在准确冻结提交创建的隔离 worktree 中运行。
- 停止时只对启动后记录的准确 PID 发送 `SIGTERM`。
