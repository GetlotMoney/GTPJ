# Evidence Routing Protocol

GTPJ workflow-v2 is a tamper-evident append-only evidence state machine.

## Core Object

The workflow routes a concrete subject, not an abstract chat conclusion:

```text
subject_id
subject_type
hypothesis_id
evidence_state
rule_checks
authority_refs
transition
```

## Authoritative History

`TRANSITIONS.jsonl` is the authoritative state history.

`evidence_routing.yaml` is only a materialized view. Its `current_state` must be derived from the chain head in `TRANSITIONS.jsonl`; it must not be hand-edited to claim a stronger state.

Each transition records:

```text
previous_transition_id
previous_transition_hash
current_transition_hash
```

The hash is computed from canonical UTF-8 JSON with sorted keys, excluding `current_transition_hash` itself.

## Transition Authority

Agents do not directly make formal facts true.

```text
Log Analyst / Result Analyst: propose transition
Interface Checker / Quality Checker / Reviewer: check transition
Coordinator: apply transition
```

Only an applied transition may update the materialized state.

## Stop And Failure

Stopping is also a transition. Failures must be structured as `transition_type: stop | block | reject | rerun`, with a `failure_type` when applicable.

## Fact Source Boundary

Campaign ledgers may index result refs, quality refs, and next actions. They must not become authoritative sources for H/U/S/ZS.

Formal facts still come from:

```text
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
ATTEMPTS.md
Warehouse logs/checkpoints/receipts
```

## Helper

Use:

```bash
python workflow/gtpj_workflow.py validate-evidence-routing
```

The helper checks transition chain continuity, hash correctness, current-state derivation, authority refs, hard-rule verdicts, and campaign result-index boundaries.
