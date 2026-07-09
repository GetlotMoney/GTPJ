# ATTEMPT-017 Monitor Handoff

本地关机后，服务器端 screen supervisor 会继续存在。它会先等待 ATTEMPT-016 训练进程结束和 GPU 空闲，再启动 ATTEMPT-017。

恢复检查命令：

```powershell
ssh -o ClearAllForwardings=yes lab4090 "screen -ls; cat /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/ATTEMPT017_SERVER_STATUS.json 2>/dev/null || true; cat /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/batch_status.json 2>/dev/null || true"
```

停止方式：

```powershell
ssh -o ClearAllForwardings=yes lab4090 "touch /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/STOP_REQUESTED"
```
