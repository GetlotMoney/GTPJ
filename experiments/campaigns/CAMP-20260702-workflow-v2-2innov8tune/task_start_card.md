# Task Start Card

```text
task_id: CAMP-20260702-workflow-v2-2innov8tune
date: 2026-07-02
owner_request: 10小时候验证整个工作流，2创新，8调参
```

## Mini Card

```yaml
owner_phrase: 10小时候验证整个工作流，2创新，8调参
task_type: mixed_experiment_campaign
base_version: v5
target: IDEA-0003 / TRIAL-001 dynamic routing follow-up
subject_id: CAMP-20260702-workflow-v2-2innov8tune
evidence_state: planning -> interface_precheck_passed after agent runtime gate
writes: experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune + .gtpj_runtime batch + Warehouse after run
agent_mode: real_multi_agent
agent_instance_mode: temporary_subagent, lifecycle campaign_scoped/task_scoped
agent_runtime_gate: agent_runtime.yaml
gates: GZSL hard rules, agent runtime hard gate, dynamic mode legality, clean freeze commit, artifact boundary, Top-3 checkpoint retention
next_action: validate agent_runtime.yaml, freeze commit, sync server, create 10-job batch, start two-GPU runner only if Runner Monitor allows
```

## Agents

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
ui_visibility: right_sidebar_temporary_agents
temporary_subagent_ids:
  campaign_planner: 019f21fe-adc2-7932-bc69-58d8c384598a
  runner_monitor: 019f21ad-89e5-72a1-b985-df3bf5ca8ca2
  interface_checker: 019f21ff-27d7-7f60-b2aa-65a80fce0a48
  evidence_quality_checker: 019f21ff-27d7-7f60-b2aa-65a80fce0a48
serial: Coordinator -> agents allow/check -> validate-agent-runtime -> freeze commit -> Runner
parallel: Campaign Planner + Runner Monitor + Interface/Evidence Quality Checker
writer_roles: Coordinator only
reviewer_roles: Interface Checker, Evidence Quality Checker, Runner Monitor
```

## Stop If

- `validate-agent-runtime` fails.
- Runner Monitor reports GPU busy or old batch still running.
- `dynamic_pse_mode` is anything other than `fixed` or `class`.
- `git diff --check` has whitespace errors beyond CRLF warnings.
- Server cannot fetch or materialize the freeze commit.
- Warehouse artifact identity or checkpoint retention cannot be recorded.
