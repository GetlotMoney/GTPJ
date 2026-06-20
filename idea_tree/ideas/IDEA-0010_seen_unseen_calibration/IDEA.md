# IDEA-0010: Seen-unseen calibration losses

```text
idea_id: IDEA-0010
status: candidate
source_type: observation
source_status: unknown
global_score: 30
current_version_score:
  v1: 30
idea_dir: idea_tree/ideas/IDEA-0010_seen_unseen_calibration/
```

## Source

Source unclear. Migrated from inactive calibration and bias-margin losses.

## Based On

- `v1`
- base logits
- GZSL seen/unseen split

## Hypothesis

Explicit seen-unseen calibration may reduce seen-class bias in generalized zero-shot evaluation.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 30 | needs_adaptation | Should wait until v1 baseline is confirmed; optimize H, not U alone. |

## Blockers

- Find GZSL calibration reference.
- Define H-based decision rule.
