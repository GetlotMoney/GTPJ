# ATTEMPT-007 Agent Summary

## Runtime Roles

| Role | Lifecycle | Agent instance | Responsibility | Pre-run decision |
|---|---|---|---|---|
| Coordinator | workflow_scoped | current Codex conversation | Final ledger writer, transition applier, owner-visible reporting | allow to prepare package |
| Runner Monitor | workflow_scoped | `019f287c-a108-7031-ba5c-6e1ae6c1c91d` | Monitor v5 completion, server sync readiness, GPU lock, and DR035 runner state | block until v5 cleanup |
| Interface Checker | task_scoped | `019f287c-65c3-74b3-b01b-84a8d3d83d38` | GZSL hard rules, seed exact-repeat boundary, tensor contract, config legality, epoch disclosure | allow |
| Evidence Quality Checker | task_scoped | `019f287c-7aee-7b72-9152-9cbba1b97bb3` | Artifact boundary, runtime gate, hash/size evidence, checkpoint retention | block until gate and v5 cleanup |
| Result Comparator | task_scoped | `019f287c-c9b8-7b81-97bd-c362025460b8` | Compare ATTEMPT-004, ATTEMPT-005, and ATTEMPT-007 criteria; report mean/min/max/range | allow |

## Coordinator Notes

- Target is ATTEMPT-004 DR-035, H=75.02, not confirmed.
- ATTEMPT-005 is a seed_sweep because it used seeds 6/7/8.
- ATTEMPT-007 must use seed 5 for all three repeats.
- Formal Runner must not start until `agent_runtime.yaml` validates and the active v5 run is complete.
- Owner-visible monitor mode is required throughout the server run.

## Pre-Run Agent Decisions

```text
Runner Monitor:
  decision: block
  blocker: v5 strict-template run is active on lab4090 and the server branch must not switch yet.

Interface Checker:
  decision: allow
  note: exact-repeat seed and GZSL interface invariants are correct; inspect generated per-job configs before launch.

Evidence Quality Checker:
  decision: block
  blocker: runtime gate and GPU/server cleanup are not closed; pre-run package structure is otherwise acceptable.

Result Comparator:
  decision: allow
  note: ATTEMPT-004/005/006/007 interpretation and thresholds are correct; do not auto-promote.
```

## Memory Policy

```yaml
memory_used: true
memory_sources:
  - Codex memory quick pass for GTPJ governance and real multi-agent gate context
verified_against_current_repo:
  - docs/workflow/START_HERE.md
  - docs/workflow/WORKFLOW_KERNEL.md
  - docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
  - docs/workflow/protocols/agent_cleanup_protocol.md
  - docs/workflow/playbooks/confirmation.md
  - experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md
  - attempts/ATTEMPT-004/result.yaml
  - attempts/ATTEMPT-005/result.yaml
formal_evidence_from_memory: false
```
