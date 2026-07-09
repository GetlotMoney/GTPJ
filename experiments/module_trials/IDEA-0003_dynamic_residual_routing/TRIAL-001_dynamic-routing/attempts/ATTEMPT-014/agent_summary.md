# ATTEMPT-014 Agent Summary

## Agent Runtime

- workflow_mode: `server_frozen_runner`
- activation_mode: `role_only`
- agent_instance_mode: `role_only`
- formal_runtime_backend: `server_detached_role_only`
- thread_creation_allowed: `false`

ATTEMPT-014 没有创建左侧命名线程，也没有启动右侧 temporary subagents。它是服务器冻结运行，用当前 owner thread 做治理、上传、启动和 closeout。

## Role Outputs

| Role | Instance | Output |
|---|---|---|
| Runner Monitor | current owner thread | `quality_check.md`, `AGENT_ACTIVITY.md` |
| Evidence Quality Checker | current owner thread | `quality_check.md` |
| Result Comparator | current owner thread | `result.yaml`, `result.md` |

## Post-Run Summary

- 有效 run：`RUN-20260708-0002-h76-restore100-exact-repeat-2gpu`
- 完成状态：80 completed / 20 skipped / 0 failed
- best single：DR-022, H=74.99, U=73.33, S=76.73
- H>=75：0
- restored candidates：12 / 20
- source_H=75.00 候选：2 个都未还原
- result_state：`tune_promising`
- promotion_decision：`blocked`

## Lessons For ATTEMPT-015

- 下一轮调参应围绕 `direction_sample + h48 + small anchor`，重点是：
  - `w=0.500, anchor=0.003`
  - `w=0.550, anchor=0.003`
  - `w=0.545, anchor=0.002`
  - `w=0.535, anchor=0.0015~0.0025`
- `w=0.515, anchor=0.004` 和 `w=0.555, anchor=0.0045` 有历史高分，但本轮 exact repeat 明显没有还原，不应继续重押。
- 本轮没有产生 promotion 或 baseline-grade evidence。

## Memory And Verification

- memory_used: no
- verified_against_current_repo: yes
- verified_against_server_batch_status: yes
- verified_against_summary_csv: yes
- verified_against_events_jsonl: yes
