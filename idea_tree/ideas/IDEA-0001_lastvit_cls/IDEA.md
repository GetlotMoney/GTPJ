# IDEA-0001: LaSt-ViT CLS replacement

```text
idea_id: IDEA-0001
status: candidate
source_type: hybrid
source_status: unverified
global_score: 55
current_version_score:
  v1: 55
idea_dir: idea_tree/ideas/IDEA-0001_lastvit_cls/
```

## Source

Code comment claims LaSt-ViT / Vision Transformers Need More Than Registers. Exact paper and official code are not verified.

## Based On

- `v1`
- Frozen CLIP ViT-L/14@336px
- patch tokens
- base logits

## Hypothesis

Replacing or blending CLIP CLS with a part-aware patch pooled CLS may improve fine-grained recognition if the pooled feature stays aligned with CLIP text space.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 55 | needs_adaptation | Potentially useful, but risky because v1 depends on CLIP-space alignment. |

## Blockers

- Verify source.
- Run shape and CLIP-alignment checks.
