# ATTEMPT-018 Log Analyst

role_key: log_analyst
thread_title: ATTEMPT-018 | Log Analyst
decision: allow

## files_reviewed

- `AGENTS.md`
- `docs/workflow/START_HERE.md`
- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/agents/shared_roles/log_analyst/profile.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/task_start_card.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/pre_run_plan.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/WORK_ITEMS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/agent_summary.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/quality_check.md`
- `.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/summary.csv`
- `.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/summary.jsonl`
- `.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/batch_status.json`
- `.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/events.jsonl`
- `.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/README.md`
- `.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu/run_dynamic_routing_batch.py`
- `workflow/gtpj_workflow.py`

## post_run_parse_plan

结论：runner 当前输出字段足以提取完成行的 `U`、`S`、`H`、`ZS`、`best_epoch`、`log_path`、`warehouse_dir`；失败阶段也可以从 runner 输出中派生，但不能只依赖 `summary.csv` 单表。

本轮 ATTEMPT-018 目标 run 是 `RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu`，当前尚未启动、也未生成本地 run 目录。跑完后按下面顺序解析：

1. 先确认 run 身份：读取 ATTEMPT-018 `manifest.yaml`、run 目录 `plan.json`、`batch_status.json`，核对 `run_id`、`profile=h76-a017dr095-restore5-exact-repeat`、`warehouse_attempt_id=ATTEMPT-018`、`base_version=v5`、`jobs=5`、`original_seed=5`、`restore_target_H=75.11`。
2. 再确认 run 是否终态：`batch_status.json` 里所有 job 必须处于 `completed`、`failed` 或 `skipped` 才能做最终日志解析；若仍有 `running` 或 `pending`，只允许输出 partial parse，不允许给 restored/near-miss 结论。
3. 读取 `summary.csv`，表头必须至少包含：`job_id`、`work_item_id`、`attempt_id`、`phase`、`group`、`name`、`seed`、`source_rank`、`resolved_from_job_id`、`status`、`U`、`S`、`H`、`ZS`、`best_epoch`、`gpu`、`log_path`、`warehouse_dir`。
4. 对每个 `status=completed` 的行，要求 `U/S/H/ZS/best_epoch/log_path/warehouse_dir` 都非空；缺任一字段时，该 job 标为 `metric_field_missing`，不能作为 clean repeat。
5. 对每个 `status=failed` 的行，不补造指标；从 `batch_status.json.jobs.<job_id>.returncode/error`、`events.jsonl` 的 `job_failed` 事件、`log_path` 指向的 `.log` 或 `.error.txt` 文件提取失败阶段和错误摘要。
6. 对每个 `status=skipped` 的行，不算 repeat 结果；优先读取 `batch_status.json` 的 `skip_reason` 或 `error`，记录为 `skipped_before_training` 或 `stop_requested_after_hit` 等派生阶段。
7. 交叉校验 `summary.csv`、`summary.jsonl`、`batch_status.json.jobs.*.metrics` 三处指标；若同一 job 的 `U/S/H/ZS/best_epoch` 不一致，阻断该 job 的 clean 解析并要求人工复核原始 log。
8. `best_epoch` 的来源应是训练日志中最后一个 `Best Results @ Epoch <n>` 段；runner 脚本当前按该规则提取，并从同一段抓取 `GZSL-U`、`GZSL-S`、`GZSL-H`、`ZSL`。
9. 输出 metrics draft 时只陈述日志事实：每个 job 的状态、U/S/H/ZS、best_epoch、log_path、warehouse_dir、失败阶段、错误摘要。是否 `best_hit`、`near_miss_not_restored`、`stable_confirm` 或 promotion，交给 Result Analyst / Coordinator，不由 Log Analyst 决定。

字段审计：

| 目标信息 | 主要来源 | 是否足够 | 解析规则 |
| --- | --- | --- | --- |
| `U` | `summary.csv` / `summary.jsonl` / `batch_status.json.jobs.*.metrics.U` | 足够 | 完成行必须非空，三处一致优先。 |
| `S` | 同上 | 足够 | 完成行必须非空，三处一致优先。 |
| `H` | 同上 | 足够 | 完成行必须非空；只作为日志事实，不直接判 promotion。 |
| `ZS` | 同上 | 足够 | 完成行必须非空，三处一致优先。 |
| `best_epoch` | `summary.csv` / `summary.jsonl` / `batch_status.json.jobs.*.metrics.best_epoch` | 足够 | 完成行必须能定位；缺失时该 job 不算 clean completed parse。 |
| `log_path` | `summary.csv.log_path` / `batch_status.json.jobs.*.log_path` | 足够 | completed/failed 行必须指向 `.log` 或 `.error.txt`；Windows 本地不可直接打开时需在服务器或 SSH 环境读取。 |
| `warehouse_dir` | `summary.csv.warehouse_dir` / `batch_status.json.jobs.*.warehouse_dir` / Warehouse `artifact_manifest.json` | 足够 | 用于定位 receipts、logs、configs、checkpoint retention manifest。 |
| `failure_stage` | 派生字段：`status` + `returncode/error/skip_reason` + `events.jsonl` + log/error 文本 | 条件足够 | CSV 没有直接列，必须派生并写明依据。 |

失败阶段派生标准：

- `train_returncode_nonzero`：`status=failed` 且 `returncode` 非 0，优先读 `log_path` 末尾错误。
- `metric_parse_failed`：训练命令返回 0，但 `H` 或 `best_epoch` 缺失，说明日志没有可用 best metric 段。
- `runner_exception`：`events.jsonl` 有 `error_log`，或 `log_path` 指向 `.error.txt`。
- `skipped_missing_source`：`status=skipped` 且错误包含 missing source/top rank。
- `stop_requested_after_hit`：`status=skipped` 且 `skip_reason=STOP_REQUESTED`，需要结合 `events.jsonl` 是否已有 restore hit。
- `unknown_failed_stage`：以上证据都不足时使用；不能硬猜。

源证据抽样校验：ATTEMPT-017 的 `DR-095` 行已在 source run `summary.csv` 中确认字段完整，值为 `U=73.00`、`S=77.36`、`H=75.11`、`ZS=82.12`、`best_epoch=48`，并含 server `log_path` 与 Warehouse `warehouse_dir`。

## blocking_issues

- 当前准备阶段无阻断；不需要启动 Runner 或修改代码即可完成跑后解析标准。
- 跑后若缺少 `summary.csv`、`batch_status.json` 或 `events.jsonl`，则阻断最终日志解析。
- 跑后若 `completed` 行缺少任一 `U/S/H/ZS/best_epoch/log_path/warehouse_dir`，则阻断该 job 作为 clean repeat 的解析。
- 跑后若 run 仍有 `running` 或 `pending` job，则只能做 partial parse，不能输出最终 restored / not_restored 判断。

## non_blocking_warnings

- `summary.csv` 没有直接 `failure_stage`、`returncode`、`error`、`skip_reason` 字段；失败阶段必须从 `batch_status.json`、`events.jsonl` 和 log/error 文件派生。
- `summary.csv` 中的路径是服务器绝对路径；如果在 Windows 本地解析原始 log，需要 SSH 到 lab4090 或使用已同步的 Warehouse 副本。
- 本轮 ATTEMPT-018 还没有实际 run 输出；以上标准基于当前 helper 代码、ATTEMPT-017 source run schema 和 ATTEMPT-018 pre-run ledger。
- exact repeat 的判断边界必须继续锁定 `seed=5`、`restore_target_H=75.11`、最多 5 次、命中即停；Log Analyst 只提取日志事实，不把 near miss 写成 restored。

## uncovered_scope

- 未启动、未监控、未解析 ATTEMPT-018 的实际 run。
- 未读取 lab4090 上的原始训练日志内容，只核查了本地 runtime cache、source summary schema 和 runner 写表逻辑。
- 未验证服务器 SSH 可达性、GPU 状态、screen 状态或 ATTEMPT-018 目标 run 目录是否已在服务器创建。
- 未做 Result Analyst 的 restored / near-miss / stable-confirm 判断。
- 未做 promotion、tag、push、delete 或任何代码修改。
