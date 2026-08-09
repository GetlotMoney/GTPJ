# ATTEMPT-013 Monitor Handoff

## 当前状态

- workflow_mode: `live_multi_agent_monitor`
- run_id: `RUN-20260707-0001-h76-followup50-live-multiagent-2gpu`
- server_batch_dir: `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260707-0001-h76-followup50-live-multiagent-2gpu`
- controller_pids: `3457554`, `3457555`
- launch_check: 2 running, 48 pending
- promotion: blocked

## 恢复监控

```bash
ssh -o ClearAllForwardings=yes lab4090 "cd /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260707-0001-h76-followup50-live-multiagent-2gpu && python3 - <<'PY'
import json
from collections import Counter
s=json.load(open('batch_status.json'))
print(s.get('status'))
print(Counter(j.get('status') for j in s.get('jobs',{}).values()))
PY
pgrep -af 'train_GTPJ_CUB|run_dynamic_routing_batch.py' || true
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits"
```

## 停止方式

不要直接杀进程，除非需要紧急停止。优先创建 stop 文件，让 controller 不再抢新 job：

```bash
ssh -o ClearAllForwardings=yes lab4090 "cd /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260707-0001-h76-followup50-live-multiagent-2gpu && printf 'owner stop request\n' > STOP_REQUESTED"
```

已启动的当前 job 会继续跑完，后续 pending job 会被标记为 skipped。

## 结果收口

完成后读取：

- `batch_status.json`
- `summary.csv`
- `summary.jsonl`
- `events.jsonl`
- `logs/`
- `runtime_configs/`

然后再写回 `result.yaml`、`result.md`、`quality_check.md`、`agent_summary.md` 和 `ATTEMPTS.md`。
