# Evidence Quality Checker Output

role: `evidence_quality_checker`
agent_instance_id: `019f3356-b57e-7282-91bc-08ac5e3304e4`
workflow_display_name: `ATTEMPT-010 | Evidence Quality Checker`
thread_title: `ATTEMPT-010 | Evidence Quality Checker`
agent_instance_mode: `named_owner_thread`
decision: `allow`

## 结论

runner_start=allow; promotion=blocked.

只允许启动 20-job same-seed min5 exact repeat。ATTEMPT-009 是 score search，四个候选目前各只有单次高分，不能作为 promotion evidence。

## 必需证据

- `agent_runtime.yaml`
- `pre_run_plan.md`
- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- `agent_summary.md`
- `AGENT_ACTIVITY.md`
- `TRANSITIONS.jsonl`
- `evidence_routing.yaml`
- 服务器 `batch_status.json`
- 服务器 `summary.csv`
- Warehouse logs/configs/checkpoints/receipts

## 质量门

- 每个候选必须 5/5 completed。
- 每个候选单独报告 best/mean/min/max/range。
- raw artifact 必须有 URI/hash/size。
- promotion 仍需 separate promotion gate。

## 线程声明

未启动 Runner / 未改文件 / 未创建子 agents。
