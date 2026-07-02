# ATTEMPT-004 Pre-Run Agent Summary

```text
attempt_id: ATTEMPT-004
subject_id: ATTEMPT-004
agent_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped / workstream_scoped / task_scoped
memory_used: yes
verified_against_current_repo: yes
persistent_thread_id: not_used
```

## Activated Agents

| Role | Agent instance | Lifecycle | Output |
|---|---|---|---|
| Workflow Coordinator | current Codex session | workflow_scoped | Applies transitions and writes GitHub ledger. |
| Runner Monitor | temporary_subagent | workflow_scoped | Checked server reachability, GPU idle state, and commit drift. |
| Interface Checker | temporary_subagent | task_scoped | Checked dynamic routing mode legality and GZSL hard-rule risk. |
| Result Planner / Tune Planner | temporary_subagent | workstream_scoped | Proposed 50-run repeat/ablation/tune/probe structure and thresholds. |
| Evidence Quality Checker | temporary_subagent | task_scoped | Checked ATTEMPT-003 evidence chain and ATTEMPT-004 launch blockers. |

## Decisions

- Use a formal 50-run mixed campaign within TRIAL-001.
- Keep this as ATTEMPT-004, not a new `vX`.
- Use `profile=dr018-confirm-ablate`.
- Start from `interface_precheck_passed` after pre-run freeze.
- Defer all result conclusions until server evidence exists.

## Agent Output Contract

All role conclusions must be preserved through:

- `pre_run_plan.md`
- `quality_check.md`
- `agent_summary.md`
- `TRANSITIONS.jsonl`
- `evidence_routing.yaml`
- post-run `manifest.yaml`, `result.yaml`, `result.md`, and Warehouse artifacts

## Memory Policy

Codex memory and prior session summaries were used only to locate known dynamic-routing pitfalls:

- server runtime copy can drift from local Git;
- batch directory existence is not execution proof;
- best single must be separated from repeat/cluster evidence;
- `dynamic_pse_mode=sample` is invalid.

Each memory-derived point was checked against current repository files, helper validation, subagent
read-only checks, or current server status before being used in the pre-run plan.
