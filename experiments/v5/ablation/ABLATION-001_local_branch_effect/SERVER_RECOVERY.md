# 服务器停止与恢复说明

## 什么时候会停止

出现以下任一情况时，控制器不再启动新的 RUN：

- 运行目录出现 `STOP` 文件；
- 控制器收到 `SIGTERM` 或 `SIGINT`；
- 任意一个已经启动的 RUN 返回非零退出码；
- 启动许可清单、冻结提交或运行前文件检查失败。

## 停止时具体做什么

控制器从正式 `training.log` 的启动标记中读取真实训练 PID。它先只向训练进程发送 `SIGTERM`，给训练进程 20 秒正常退出，并让外层账本 helper 写完失败日志、结束标记和收据。训练进程不退出时，再发送 `SIGKILL`，最多等待 5 秒。

如果训练 PID 还没来得及写入日志，控制器才会停止整个 helper 进程组，并在状态中写入 `stop_evidence_state: incomplete_before_training_pid`。这种运行不能作为正式结果。

## 停止后留下什么

- `status.json`：控制器和六个 RUN 的最终状态、helper PID、训练 PID、停止方式；
- `recovery_handoff.json`：需要人工处理的 RUN、原账本副本和下一步动作；
- 每个已启动 RUN 的 `run_start_receipt.json`、`run_start_receipt.finish.json`、`training.log` 和 `helper.log`（能正常收口时）；
- Warehouse 中已经产生的模型、checkpoint 和训练日志，全部保留，不自动删除。

## 恢复规则

半截运行不允许原目录自动续跑，也不允许把同一个 `run_id` 重新启动。先把停止或失败的收据同步回正式账本，再新建一行冻结 RUN：

1. 新 RUN 使用新的 `job_id` 和 `run_id`；
2. `repeat_of` 指向被停止的原 RUN；
3. 默认从头训练，不能从旧 checkpoint 续训；
4. 使用新的 runtime 和 Warehouse 目录；
5. 重新完成参数表冻结、审核、运行许可清单和服务器预检。

这样做会多跑一次，但不会把半截训练和完整训练混成同一个实验结果。

## 人工停止方式

在服务器运行目录创建空文件：

```bash
touch <runtime-root>/STOP
```

随后检查：

```bash
cat <runtime-root>/status.json
cat <runtime-root>/recovery_handoff.json
```

只有 `status.json` 中两个正在运行的任务都退出，并且 GPU 上不再存在对应 PID，才算停止完成。
