# 暂停与监控交接

如果当前对话暂停，服务器 detached 控制器继续按冻结提交运行，不由新任务重新启动。恢复查看时只读取下列权威文件：

- runtime 目录的 `status.json` 和 `controller.pid`；
- runtime 目录的 `STOP` 与 `recovery_handoff.json`；
- Warehouse 各 RUN 的 `helper.log`、`training.log`、启动/结束收据；
- 固定领取目录里的 execution claim 与 controller failure 记录。

只有用户在当次消息明确要求停止时，才创建 `STOP`。不得杀死不属于本实验进程组的 PID，不得复用旧 `run_id`，不得在半截目录上续跑。恢复后的首条汇报要说明两个 GPU 当前 RUN、最新 epoch、日志是否增长、是否存在 NaN/异常，以及已完成 RUN 的收据状态。
