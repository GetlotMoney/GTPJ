# Agent Summary

```text
campaign_id: CAMP-20260702-workflow-v2-2innov8tune
run_id: RUN-20260702-0003-mixed2innov8tune-2gpu
base_version: v5
subject_id: CAMP-20260702-workflow-v2-2innov8tune
subject_type: campaign
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: campaign_scoped
ui_visibility: right_sidebar_temporary_agents
agent_runtime_gate: agent_runtime.yaml
temporary_subagent_ids: campaign_planner=019f21fe-adc2-7932-bc69-58d8c384598a; runner_monitor=019f21ad-89e5-72a1-b985-df3bf5ca8ca2; interface_quality=019f21ff-27d7-7f60-b2aa-65a80fce0a48
runner_start_gate: allow after freeze commit is synced to lab4090
final_decision: allow_after_freeze_sync
```

## Campaign Planner

```text
role: Campaign Planner
agent_instance_id: 019f21fe-adc2-7932-bc69-58d8c384598a
decision: warn
reason_summary: Candidate direction is acceptable for planning; formal Runner requires clean gate and server readiness.
blocking_issues: dirty tree before freeze; missing agent_runtime before this campaign file set.
```

## Interface / Evidence Quality Checker

```text
role: Interface Checker + Evidence Quality Checker
agent_instance_id: 019f21ff-27d7-7f60-b2aa-65a80fce0a48
decision: warn after gate creation
reason_summary: GZSL and dynamic mode rules appear satisfiable; agent_runtime.yaml passes validation and records real temporary agent ids. quality_check.md was refreshed to allow after freeze sync.
blocking_issues: none after gate creation; server sync must still be verified before formal Runner start.
```

## Runner Monitor

```text
role: Runner Monitor
agent_instance_id: 019f21ad-89e5-72a1-b985-df3bf5ca8ca2
decision: warn after old batch completion
reason_summary: Old RUN-20260702-0002 is complete, both GPUs are free, and RUN-20260702-0003 is not occupied.
blocking_issues: none for server/GPU; server commit sync must be verified before launch.
```
