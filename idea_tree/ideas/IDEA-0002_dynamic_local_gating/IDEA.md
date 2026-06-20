# IDEA-0002: Dynamic local branch gating and pooling

```text
idea_id: IDEA-0002
status: candidate
source_type: observation
source_status: unknown
global_score: 45
current_version_score:
  v1: 45
idea_dir: idea_tree/ideas/IDEA-0002_dynamic_local_gating/
```

## Source

Source unclear. Migrated from inactive code switches.

## Based On

- `v1`
- base logits
- local_score
- score_s2v / score_v2s

## Hypothesis

Input-dependent gating may reduce harmful local branch influence on easy samples while keeping local evidence for hard samples.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 45 | needs_adaptation | Useful only if split into one-variable trials; multiple gates together are hard to interpret. |

## Blockers

- Record source or local rationale.
- Split dynamic gate, branch weight, and pooling into separate ideas or trials.
