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
- `EXPERIMENT.yaml`。

控制器先把 Git bundle 解入操作系统临时目录中的隔离校验仓，核对实验分支和准确提交，
重新计算上述哈希。执行代码包里的 `workflow/gtpj_workflow.py` 前，还必须证明该文件的 Git
对象与控制器硬编码信任的冻结 V5 母版完全相同；代码包如果替换了校验器，会在执行它之前
直接失败。随后才运行审核、运行时、参数矩阵、实验绑定和仓库边界校验。这个阶段不会建立
正式运行副本，也不会创建训练进程。只有全部通过，才会继续服务器 GPU 预检。

每次正式执行使用：

```text
execution_id = V5-ABLATION-001-<冻结提交前12位>
```

runtime 与 Warehouse 目录都必须以这个 `execution_id` 命名，并且开始时完全不存在。它们
还必须分别直接位于固定的服务器父目录，命令行不能换一个父目录绕过检查。控制器只在固定的
`/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/ablation/.gtpj_execution_claims/`
中一次性领取 `execution_id` 和六个 `run_id`。领取记录不会自动删除；即使旧目录被人工搬走，
相同身份也不能再次启动。

## 什么时候会停止

出现以下任一情况时，控制器不再启动新的 RUN：

- 运行目录出现 `STOP` 文件；
- 控制器收到 `SIGTERM` 或 `SIGINT`；
- 任意一个已启动 RUN 返回非零退出码；
- 启动证据、冻结提交、GPU 预检或运行前文件检查失败。

signal handler 只设置内存中的停止事件，不直接写文件、不获取状态锁。`STOP` 文件、状态变更
和进程终止都由普通控制流程完成，避免信号恰好打断文件锁时发生自锁。

## 停止时具体做什么

控制器从正式 `training.log` 的启动标记读取真实训练 PID。它先向训练进程发送 `SIGTERM`，
给账本 helper 写完失败日志、结束标记和收据的机会；训练没有收口时再发送 `SIGKILL`。

如果训练 PID 尚未写入日志，控制器会停止整个 helper 进程组，并记录：

```text
process_evidence_state: incomplete_before_training_pid
```

如果停止真实训练 PID 时发生异常，控制器仍会在统一 `finally` 清理中继续停止 helper 进程组。
只有确认进程树已经退出，`cleanup_complete` 才能为 `true`。

结束收据无效、状态落盘失败或清理不完整一经发现，会先在共享启动锁中登记失败，再继续写状态
或向上抛错；另一张卡不能利用异常处理的时间窗口领取下一项 RUN。

每个已启动 RUN 的 `run_start_receipt.finish.json` 还会再次核对：JSON 结构、`job_id`、
`run_id`、启动收据哈希、退出码、PID 和日志哈希。文件只存在但内容对不上，仍然属于证据不完整，
不能作为正式结果。

## 停止后留下什么

- `status.json`：控制器和六个 RUN 的最终状态、helper PID、训练 PID、清理结果和收据状态；
- `recovery_handoff.json`：需要处理的 RUN、旧账本副本和下一步动作；
- `.gtpj_execution_claims/<execution_id>.json`：不可重复使用的执行身份和六个 `run_id`；
- 每个已启动 RUN 的启动收据、结束收据、训练日志和 helper 日志；
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
