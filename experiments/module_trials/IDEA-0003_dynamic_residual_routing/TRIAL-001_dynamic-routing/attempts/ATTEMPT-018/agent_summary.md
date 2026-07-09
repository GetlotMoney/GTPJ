# ATTEMPT-018 Agent Summary

status: completed_not_restored
workflow_mode: `live_multi_agent_monitor`
agent_instance_mode: `named_owner_thread`
memory_used: true
verified_against_current_repo: partial

## Active Roles

- Coordinator: current owner thread
- Reviewer: allow, thread `019f4509-51a5-7ba1-9b64-0d6ed5df4464`
- Runner Monitor: allow, thread `019f4509-712b-7142-b443-9bbbc7675124`
- Interface Checker: allow, thread `019f4509-926b-7c20-b9aa-5e9cb09438c1`
- Evidence Quality Checker: allow, thread `019f4509-9f62-7260-a4df-61738d7fde9a`
- Log Analyst: allow, thread `019f4509-aaca-7c42-8467-adc20316e355`
- Result Analyst: allow, thread `019f4509-b77c-7503-9547-5ca0fc620067`

## Current Decision

Formal Runner completed on lab4090. Named threads and role outputs existed for the live multi-agent pre-run gate, all five repeat jobs completed, and no job restored `H=75.11`.

Closeout:

- completed: 5/5
- failed: 0
- skipped: 0
- best repeat: DR-001, H=74.71
- mean_H: 74.58
- confirmation_decision: `not_restored`
- evidence_state: `stopped_repeat_unstable`
- promotion_decision: `blocked`

Source-control caveat: ATTEMPT-018 was launched before the later source-control helper hardening. Treat it as observed repeat evidence, not as a post-fix restored/promotion claim.
