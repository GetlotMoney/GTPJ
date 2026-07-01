# GTPJ Workflow Kernel

This file is the compact hard-rule layer. It should stay short.

## 1. Authority

- GitHub is the reproducibility control plane, governance ledger, and lightweight result index.
- `GTPJ_Research` stores long reasoning, paper/source notes, and full idea history.
- `GTPJ_Warehouse` stores raw logs, checkpoints, generated figures, run receipts, and large artifacts.
- Chat context, temporary agent context, persistent thread context, and Codex memory are orientation only. They are not formal evidence.

## 2. Formal Evidence Boundary

A task is formal evidence work if it can affect any of these:

```text
manifest/result/quality/agent_summary
ATTEMPTS keep/drop/reject/rerun
best or top-k selection
repeat/confirmation
promotion/version/tag decision
paper/baseline claim
next expensive run
code/config/eval semantics
```

Formal evidence work requires `real_multi_agent` unless the owner explicitly downgrades it to debug/smoke.

## 3. Agent Rule

Default formal agent mode:

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

Meaning:

- Each role gets isolated live context during the workflow or campaign stage.
- Role lessons that must persist are written to `agent_summary.md`, role `memory.md`, workflow issues, result files, or campaign ledgers.
- `persistent_thread` is optional for visible cross-workflow tracking, but it is not evidence.
- Do not create one permanent agent/thread per experiment run.
- Use clear role names, for example `Runner Monitor`, `Log Analyst`, `Evidence Quality Checker`, `Result Comparator`.

Writer boundaries:

- Coordinator is the final GitHub ledger writer.
- Runner owns server/GPU execution state.
- Only one Implementer may edit a given code path.
- Reader/Planner, Log Analyst, Quality Checker, Result Analyst, Interface Checker, and Reviewer are read-only unless explicitly assigned otherwise.

## 4. Versioning Rule

- Parameter tuning alone does not create a new `vX`.
- A new `vX` requires a confirmed promoted framework or method state, not just a tuned config.
- Confirmation should normally run 3 repeats. If repeats pass, the official reported single value is the best repeat, while mean/min/max remain part of the evidence.
- Do not call an unconfirmed `best_observed_H` a confirmed baseline.

## 5. Run Safety

Before a formal run:

```text
record branch and commit
record git dirty state
freeze config
record dataset/split/label mapping assumptions
lock GPU or runner slot
define result/artifact location
define checkpoint retention rule
```

Hard block if label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear.

## 6. Checkpoint Retention

Workflow norm:

```text
After each experiment round, delete non-kept checkpoints.
Keep only the best 3 model checkpoints unless a playbook explicitly says otherwise.
Never delete logs, manifests, result files, quality checks, or Warehouse receipts.
```

Deletion must be scoped to generated experiment checkpoints, never user data or source history.

## 7. Promotion Gate

Promotion can start only when evidence explicitly supports it:

```text
promotion_decision: promote
complete manifest/result/quality/interface evidence
repeat or confirmation evidence when required
target version declared
no unresolved hard gate
```

Promotion may create local commits/tags when the protocol requires it. It must not push unless the owner asks.

## 8. Stop Rule

Stop or downgrade when:

- required evidence is missing,
- server/runtime state is ambiguous and could corrupt results,
- a workflow asks for formal multi-agent work but real multi-agent support is unavailable,
- the owner changes the scope,
- a safety boundary would be crossed.

When stopped, report the smallest unblock action.
