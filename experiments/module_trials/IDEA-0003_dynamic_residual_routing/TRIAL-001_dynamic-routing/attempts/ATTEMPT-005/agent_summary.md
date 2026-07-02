# ATTEMPT-005 Agent Summary

## Runtime Roles

| Role | Lifecycle | Agent instance | Responsibility | Pre-run decision |
|---|---|---|---|---|
| Coordinator | workflow_scoped | current Codex conversation | Final ledger writer, transition applier, owner-visible reporting | allow |
| Runner Monitor | workflow_scoped | `019f239f-6081-7d92-b347-047bb0503ea8` | Server sync, GPU lock, queue/process monitoring | pass after freeze/sync |
| Interface Checker | task_scoped | `019f239f-90e5-7fd3-94ac-3f10900ed1c8` | GZSL hard rules, tensor contract, config legality, epoch disclosure | pass, runtime gate required |
| Evidence Quality Checker | task_scoped | `019f239f-c37c-75e3-8a2a-b5c6e0ffbe6b` | Artifact boundary, hash/size evidence, checkpoint retention | pass, runtime gate required |
| Log Analyst | run_scoped | pending after run | Parse runtime logs and summary files | not_checked |
| Result Comparator | task_scoped | `019f23a5-8c8a-7c50-a076-f1b93160a2e4` | Compute repeat mean/min/max/range and recommend state | warn; stability not exact H=75.02 |

## Coordinator Notes

- Target is ATTEMPT-004 DR-035, H=75.02, not confirmed.
- ATTEMPT-005 is a min3 confirmation run with three frozen repeats and no tuning.
- Formal Runner must not start until `agent_runtime.yaml` contains real temporary agent ids and validates.
- Owner-visible monitor mode is required throughout the server run.

## Pre-Run Agent Decisions

```text
Runner Monitor:
  decision: block before freeze/sync; GPU idle, no old runner, run dir absent.
  resolution: complete pre-run freeze commit, sync lab4090, then start Runner.

Interface Checker:
  decision: block before agent_runtime gate; GZSL/logits/PSE/epoch checks pass.
  resolution: write real agent_runtime.yaml and validate it.

Evidence Quality Checker:
  decision: block before agent_runtime gate and clean freeze; evidence boundary is correct.
  resolution: validate runtime gate, freeze commit, register post-run artifacts.

Result Comparator:
  decision: warn; target is DR-035 stability, not exact H=75.02 reproduction.
  resolution: report official_single as best repeat and stability as mean/min/max/range.
```

## Memory Policy

```yaml
memory_used: true
memory_sources:
  - Codex memory quick pass for TRIAL-001 dynamic-routing workflow conventions
verified_against_current_repo:
  - experiments/campaigns/CAMP-20260702-workflow-v2-2innov8tune/FINAL_REPORT.md
  - experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml
  - docs/workflow/AGENT_RUNTIME_HARD_GATE.md
  - docs/workflow/GZSL_HARD_RULES.md
formal_evidence_from_memory: false
```
