# 监控交接

- 实验：`V5-CONFIRM-002`
- 运行方式：服务器后台运行，两张 GPU，三波 `2+2+1`
- 状态入口：服务器 runtime 目录的 `status.json`
- 停止方式：在 execution runtime 目录创建 `STOP`，或向控制器发送 `SIGTERM`
- 当前状态：启动前冻结完成，等待服务器最终验证和第一波启动
- 汇报渠道：当前对话
