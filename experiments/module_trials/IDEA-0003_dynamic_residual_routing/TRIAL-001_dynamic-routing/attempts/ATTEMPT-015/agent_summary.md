# ATTEMPT-015 Agent Summary

## Runtime

- workflow_mode: `live_multi_agent_monitor`
- activation_mode: `real_multi_agent`
- agent_instance_mode: `named_owner_thread`
- formal_runtime_backend: `named_owner_thread`
- thread_creation_allowed: `true`
- right_side_temporary_subagent_used: `false`

## Role Outputs

| Role key | Thread id | Output | Decision |
|---|---|---|---|
| tune_planner | 019f404b-b83a-7d81-9128-9cc6f8de51c0 | `agent_outputs/tune_planner.md` | allow |
| evidence_quality_checker | 019f404b-d419-7800-aec5-bc0fac87bae4 | `agent_outputs/evidence_quality_checker.md` | allow |
| result_comparator | 019f404b-f4b0-7952-920f-06b1332ed5f0 | `agent_outputs/result_comparator.md` | allow |
| runner_monitor | 019f404c-0215-7ab3-9c78-4148854135fa | `agent_outputs/runner_monitor.md` | allow |
| interface_checker | 019f405c-8b4e-72d0-b93a-8c03b76522e1 | `agent_outputs/interface_checker.md` | allow |

## Decision

All pre-run roles allow ATTEMPT-015 as a 100-job tune_search. The formal runner completed on lab4090.

Final live monitor snapshot: 100 completed, 0 running, 0 pending. `DR-004` remains best with H=75.04, and `DR-035` also reached H=75.00 as a tune_search single-run hit. H>=76 did not appear. These results are useful for follow-up exact-repeat planning only; they are not confirmation or promotion evidence.

Promotion remains blocked. Confirmation remains not started.

## Cleanup Policy

During `live_multi_agent_monitor`, active left-sidebar named threads remain visible while the Runner still has running or pending jobs. Completed threads are archived only after closeout/handoff and evidence writeback.

## Archive Result

All five completed left-sidebar named Codex threads were archived after server runner start, then reopened after owner clarification that active `live_multi_agent_monitor` runs should keep left-sidebar named agents visible until closeout:

- tune_planner: `019f404b-b83a-7d81-9128-9cc6f8de51c0`
- evidence_quality_checker: `019f404b-d419-7800-aec5-bc0fac87bae4`
- result_comparator: `019f404b-f4b0-7952-920f-06b1332ed5f0`
- runner_monitor: `019f404c-0215-7ab3-9c78-4148854135fa`
- interface_checker: `019f405c-8b4e-72d0-b93a-8c03b76522e1`

Final archive completed after ATTEMPT-015 closeout-check passed and `agent-cleanup-plan` returned `ARCHIVE` for all five named threads.

## Live Reporting

`monitor-workflow --report-new-completions` is enabled for this run. The local de-duplication file is:

```text
.gtpj_runtime/batches/RUN-20260708-0003-h76-hotspot100-tune-live-multiagent-2gpu/monitor_seen_completed_jobs.json
```

Formal facts remain `summary.csv/jsonl`, `batch_status.json`, logs, Warehouse artifacts, and the attempt ledgers.
