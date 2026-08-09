# ATTEMPT-014 Monitor Handoff

## 当前有效状态

- 有效远端 run：`RUN-20260708-0002-h76-restore100-exact-repeat-2gpu`
- 远端目录：`/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260708-0002-h76-restore100-exact-repeat-2gpu`
- detached screen：`GTPJ_ATTEMPT014_RESTORE100_R2`
- 启动时状态：`running: 2, pending: 98`
- 服务器 commit：`d505e992492eb6fe7272edf0f0dc1d15a5932434`
- `git_remote`: `none`
- 旧 run `RUN-20260708-0001-h76-restore100-exact-repeat-2gpu` 是启动环境失败，不是方法证据。

## 关机后恢复查看

```powershell
ssh -o ClearAllForwardings=yes lab4090 "screen -ls; cd /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260708-0002-h76-restore100-exact-repeat-2gpu && python3 -c \"import json, collections; data=json.load(open('batch_status.json')); print(data.get('status'), dict(collections.Counter(j.get('status','unknown') for j in data.get('jobs',{}).values())))\""
```

如果 `screen` 已经结束，不代表失败；继续以 `batch_status.json`、`summary.csv/jsonl`、`events.jsonl` 和 controller logs 判断最终结果。

当前状态：pre-run planned，本地 frozen plan 待生成/验证，服务器未启动。

恢复检查本地计划：

```powershell
cd D:\Backup\Documents\Myself\GTPJ
python workflow\gtpj_workflow.py dynamic-routing-status --run-dir .gtpj_runtime\batches\RUN-20260708-0001-h76-restore100-exact-repeat-2gpu
```

服务器启动后才使用远端恢复命令；当前没有远端 run 事实。
