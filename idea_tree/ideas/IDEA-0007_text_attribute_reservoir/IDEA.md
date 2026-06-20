# IDEA-0007: Topology-aware text attribute reservoir

```text
idea_id: IDEA-0007
status: candidate
source_type: observation
source_status: unknown
global_score: 45
current_version_score:
  v1: 45
idea_dir: idea_tree/ideas/IDEA-0007_text_attribute_reservoir/
```

## Source

Source unclear. Migrated from inactive `use_text_attr_reservoir` switch.

## Based On

- `v1`
- GPT text prototypes
- CUB expert attributes
- CLIP attribute text
- topology-preserving text constraint

## Hypothesis

Injecting attribute-text reservoir information into class prototypes may enrich semantics while topology loss limits drift.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 45 | needs_adaptation | Potentially useful but can distort GPT/CLIP text geometry. |

## Blockers

- Clarify source.
- Check text topology drift.
