# IDEA-0004: AG-JEPA neighbor-text variant

```text
idea_id: IDEA-0004
status: candidate
source_type: observation
source_status: unknown
global_score: 40
current_version_score:
  v1: 40
idea_dir: idea_tree/ideas/IDEA-0004_ag_jepa_neighbor_text/
```

## Source

Source unclear. Migrated from inactive `use_ag_jepa_v2` switch.

## Based On

- `v1`
- AG-JEPA auxiliary training
- GPT text prototypes

## Hypothesis

Adding nearby class text as a neighbor constraint may make AG-JEPA patch prediction less class-isolated and improve semantic smoothness.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 40 | direct | v1 already uses AG-JEPA, so this is a local extension. |

## Blockers

- Decide whether this is local or paper-backed.
- Check fine-grained class blurring.
