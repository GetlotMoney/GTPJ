# IDEA-0003: Cosine-only CrossModal scoring with anchor losses

```text
idea_id: IDEA-0003
status: candidate
source_type: observation
source_status: unknown
global_score: 35
current_version_score:
  v1: 35
idea_dir: idea_tree/ideas/IDEA-0003_cosine_only_scoring/
```

## Source

Source unclear. Migrated from inactive `cosine_only` path.

## Based On

- `v1`
- CrossModalTransformer
- Text Adapter
- base logits

## Hypothesis

Direct CrossModal cosine scoring may outperform additive correction if anchor losses prevent CLIP-space drift.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 35 | needs_adaptation | High risk because it changes the main scoring path. |

## Blockers

- Strict source/rationale review.
- Shape check and unseen-geometry check.
