# ATTEMPT-016 Monitor Handoff

恢复检查命令：

```powershell
ssh -o ClearAllForwardings=yes lab4090 "screen -ls; cat /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260708-0005-h76-hotspot-top2-restore10-exact-repeat-2gpu/batch_status.json"
```

若服务器 Runner 启动后本地会话中断，以 `batch_status.json`、`summary.csv`、`summary.jsonl` 和 `events.jsonl` 为准。
