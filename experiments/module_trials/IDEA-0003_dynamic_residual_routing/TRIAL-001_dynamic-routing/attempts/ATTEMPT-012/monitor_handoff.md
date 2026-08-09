# ATTEMPT-012 Monitor Handoff

## 恢复检查命令

```powershell
ssh -o ClearAllForwardings=yes lab4090 "screen -ls; cat /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu/batch_status.json"
```

## Workflow 监控入口

服务器是真实训练位置，本地 `.gtpj_runtime` 是 workflow monitor 的控制面镜像。每次使用 `monitor-workflow` 前，先同步服务器状态：

```powershell
scp lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu/batch_status.json .gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu/batch_status.json
scp lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu/events.jsonl .gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu/events.jsonl
python workflow/gtpj_workflow.py monitor-workflow --run-dir .gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu --top-k 5 --max-polls 1
```

如果 `summary.csv` 或 `summary.jsonl` 已出现，也一并同步后再跑 `monitor-workflow`，这样 best/top-k 才会显示。

## 结果文件

- Server batch: `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260706-0005-h76-followup50-multiseed-2gpu`
- Status: `batch_status.json`
- Events: `events.jsonl`
- Summary: `summary.csv` / `summary.jsonl`
- Logs: `logs/controller_*.log`

如果 screen session 已结束，仍以 batch 文件判断是否完成。
