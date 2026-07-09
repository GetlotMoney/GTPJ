# ATTEMPT-011 Monitor Handoff

## 本地关机后的恢复命令

重新开机后，只读检查服务器状态：

```powershell
ssh -o ClearAllForwardings=yes lab4090 "screen -ls; cat /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/ATTEMPT-011_SERVER_STATUS.json"
```

如果 `screen` session 已结束，不代表失败；继续读取每个 batch 的：

- `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/<RUN_ID>/batch_status.json`
- `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/<RUN_ID>/summary.csv`
- `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/<RUN_ID>/summary.jsonl`
- `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/<RUN_ID>/events.jsonl`

## 停止命令

要停止后续新 job，不杀进程，创建 stop 文件：

```bash
touch /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/<RUN_ID>/STOP_REQUESTED
```

已开始训练的 job 会继续完成；未开始的 job 由 controller 标记为 `skipped`。

## 不要做的事

- 不要用本地 Codex 线程常驻监控服务器。
- 不要因为 `screen -ls` 为空就重启 batch。
- 不要用右侧栏临时 agents 补 formal gate。
- 不要在没有读取 `batch_status.json` / `summary.csv` 的情况下判断结果。
