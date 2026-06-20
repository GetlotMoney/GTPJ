# IDEA-0008: Attribute-patch OT alignment

```text
idea_id: IDEA-0008
status: candidate
source_type: hybrid
source_status: unverified
global_score: 50
current_version_score:
  v1: 50
idea_dir: idea_tree/ideas/IDEA-0008_attr_patch_ot/
```

## Source

Uses optimal-transport style Sinkhorn matching, but the exact GTPJ module source is not verified.

## Based On

- `v1`
- FAE geometry-aware local encoding
- CUB expert attributes
- CLIP attribute text

## Hypothesis

Soft OT alignment between local patches and class-relevant attributes may improve fine-grained part grounding.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 50 | direct | v1 has FAE patches and attribute text inputs. |

## Blockers

- Verify OT/patch-attribute grounding source.
- Check numerical stability.
