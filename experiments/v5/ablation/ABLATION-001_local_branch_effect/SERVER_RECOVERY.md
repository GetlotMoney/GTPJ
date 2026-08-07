# 服务器停止与恢复说明

## 适用环境

正式控制器只允许在 Linux 服务器运行，因为它必须使用真实进程组、`SIGTERM` 和
`SIGKILL`。Windows 本机可以运行单元测试，但不能启动本次正式训练，避免把两种不同的
停止语义混在一起。

## 启动前怎样防止误跑

外部 `launch_manifest.json` 不再用一组“已通过”布尔值自我证明。它只记录冻结提交、
实验分支、V5 母版提交、六个 `run_id`，以及下列冻结文件的 SHA-256：

- `TASK_START.yaml`；
- `agent_runtime.yaml`；
- strict-3 审核最终决定；
- `PARAMETER_MATRIX.csv`；
- `EXPERIMENT.yaml`；
- `DATA_MANIFEST.json`。

清单还固定服务器 Python 路径和 SHA-256。`DATA_MANIFEST.json` 恰好记录 12 个正式
CUB/xlsa17 输入文件的相对路径、大小和 SHA-256，以及 split、label、class order 和 metric
口径。控制器会先在固定源目录逐个重算，再把 12 个文件复制到本次 execution 的
`data_snapshot/`；复制过程中再次核对大小和完整 SHA-256，完成后把文件与目录改为只读。FULL 和
GLOBAL_ONLY 都只链接这同一份私有快照；每个 RUN 启动前再次重算快照内容，训练入口加载时还会自行
重算输入哈希并检查缓存标签与 xlsa17 划分逐元素一致。源目录在预检后变化不会进入本次训练。

控制器先把 Git bundle 克隆为带 `.git` 的临时隔离校验仓，切到准确实验分支和提交，
重新计算上述哈希。执行代码包里的 `workflow/gtpj_workflow.py` 前，还必须证明该文件的 Git
对象是冻结 V5 母版版本，或控制器硬编码的已审核绑定运行时版本；其他替换会在执行前直接失败。
随后才运行审核、运行时、参数矩阵、实验绑定和仓库边界校验。这个阶段不会建立
正式运行副本，也不会创建训练进程。只有全部通过，才会继续服务器 GPU 预检。

正式 Python 在核对路径和 SHA-256 后会被打开并保持到控制器退出。helper、训练包装器和最终训练
入口都通过这个文件描述符执行，而不是重新相信可变路径。这样即使检查后原路径被替换，实际运行
的仍是已经核对过的解释器。

每次正式执行使用：

```text
execution_id = V5-ABLATION-001-<冻结提交前12位>
```

runtime 与 Warehouse 目录都必须以这个 `execution_id` 命名，并且开始时完全不存在。它们
还必须分别直接位于固定的服务器父目录，命令行不能换一个父目录绕过检查。控制器只在固定的
`/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/ablation/.gtpj_execution_claims/`
中一次性领取 `execution_id` 和六个 `run_id`。领取记录不会自动删除；即使旧目录被人工搬走，
相同身份也不能再次启动。

领取记录不会直接向最终文件边写边发布。控制器先在同目录把完整 JSON 写入临时文件并执行
`fsync`，再用不可覆盖的硬链接原子发布；写入或发布失败时会尽力清理临时文件，不会留下空的正式
claim。正式 claim 已发布后，即便临时文件因文件系统异常暂时删不掉，控制器仍保留并返回正式 claim，
不会丢失恢复凭证。

## 什么时候会停止

出现以下任一情况时，控制器不再启动新的 RUN：

- 运行目录出现 `STOP` 文件；
- 控制器收到 `SIGTERM` 或 `SIGINT`；
- 任意一个已启动 RUN 返回非零退出码；
- 启动证据、冻结提交、GPU 预检或运行前文件检查失败。

signal handler 只设置内存中的停止事件，不直接写文件、不获取状态锁。`STOP` 文件、状态变更
和进程终止都由普通控制流程完成，避免信号恰好打断文件锁时发生自锁。
每项 RUN 在 Python 与数据完整复核结束后，先准备目录、环境变量和 helper 日志；随后在创建 helper
的同一把锁里再次检查 STOP 和停止事件，检查通过后的第一项动作就是创建 helper。这样，耗时校验
或启动准备期间收到停止请求都不会继续创建新进程。

## 停止时具体做什么

控制器从正式 `training.log` 的启动标记读取真实训练 PID，用 Linux `/proc` 核对 PID、进程组、
会话和启动时钟，再打开 pidfd 绑定具体进程对象。它先通过 pidfd 向训练进程发送 `SIGTERM`，
给账本 helper 写完失败日志、结束标记和收据的机会；训练没有收口时再发送 `SIGKILL`。

如果训练 PID 尚未写入日志，控制器会为同一受信会话的进程逐一打开 pidfd 后停止，并记录：

```text
process_evidence_state: incomplete_before_training_pid
```

如果停止真实训练 PID 时发生异常，控制器仍会在统一 `finally` 清理中继续停止 helper 会话。
即使 helper 已先退出，只要同一受信会话里还有训练子进程，控制器仍会停止整个进程组。只有确认
进程组已空、helper 已回收且没有 PID 身份冲突，`cleanup_complete` 才能为 `true`。

如果 helper 刚创建就无法捕获身份，控制器不会先 `wait` 它；此时直接子进程 PID 还不可能复用，
控制器会立即强制停止其独立进程组、回收 helper 并写不可覆盖的启动失败记录。

结束收据无效、状态落盘失败或清理不完整一经发现，会在共享启动锁内同时登记失败。包括最终
`completed` 状态在内的所有关键状态写入都通过同一把锁；另一张 GPU 的 worker 在领取下一项前必须
取得同一把锁，因此不能利用异常处理窗口启动后续 RUN。

如果 helper 已创建但首次 `running` 状态无法落盘，控制器会在仍持有启动锁时立即清理该 helper，
并在本项 RUN 目录写入不可覆盖的 `launch_failure.json`，记录 helper PID、原始状态错误和完整清理
结果。`cleanup_complete` 不是 `true` 时会明确报“进程树清理不完整”，不会丢掉 PID 或把它伪装成
普通状态写入失败。

每个已启动 RUN 的 `run_start_receipt.finish.json` 还会再次核对：JSON 结构、`job_id`、
`run_id`、启动收据哈希、退出码、PID 和日志哈希。文件只存在但内容对不上，仍然属于证据不完整，
不能作为正式结果。

## 停止后留下什么

- `status.json`：控制器和六个 RUN 的最终状态、helper PID、训练 PID、清理结果和收据状态；
- `recovery_handoff.json`：需要处理的 RUN、旧账本副本和下一步动作；
- `.gtpj_execution_claims/<execution_id>.json`：不可重复使用的执行身份和六个 `run_id`；
- `.gtpj_execution_claims/<execution_id>.failure.json`：领取身份后建目录、克隆或状态写入失败时的不可覆盖凭证；
- 每个已启动 RUN 的启动收据、结束收据、训练日志和 helper 日志；
- 首次运行状态落盘失败时的 `launch_failure.json`；
- Warehouse 中已经产生的模型、checkpoint 和训练日志，全部保留，不自动删除。

## 恢复规则

半截运行不允许在原目录自动续跑，也不允许复用冻结提交或旧 `run_id`。先把停止或失败证据
同步回正式账本，然后重新规划：

1. 创建新的 `job_id` 和 `run_id`；
2. 新行的 `repeat_of` 指向被停止的旧 RUN；
3. 默认从头训练，不从旧 checkpoint 续训；
4. 完成新的审核与运行门记录；
5. 生成新的冻结提交，因此得到新的 `execution_id`；
6. 使用全新的 runtime 和 Warehouse 目录。

这样会增加一次运行成本，但不会把半截训练和完整训练混成同一个实验结果。

## 人工停止方式

在服务器本次运行目录创建空文件：

```bash
touch <runtime-root>/STOP
```

随后检查：

```bash
cat <runtime-root>/status.json
cat <runtime-root>/recovery_handoff.json
```

只有两张卡上属于本次实验的训练进程都已经退出，且每个已启动 RUN 都记录了
`cleanup_complete: true`，才算停止完成。证据不完整的 RUN 必须按上面的恢复规则新建，不能原地重试。
