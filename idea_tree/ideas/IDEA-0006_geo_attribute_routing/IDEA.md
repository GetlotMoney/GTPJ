# IDEA-0006: Geometry-aware attribute routing

```text
idea_id: IDEA-0006
status: candidate
source_type: observation
source_status: unknown
global_score: 50
current_version_score:
  v1: 50
idea_dir: idea_tree/ideas/IDEA-0006_geo_attribute_routing/
```

## Source

Source unclear. Migrated from inactive `use_geo_attr_routing` switch.

## Based On

- `v1`
- FAE geometry-aware local encoding
- CUB expert attributes
- CLIP attribute text

## Hypothesis

Routing local visual features to class-relevant attribute text may improve explainable part-attribute grounding.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 50 | direct | v1 already passes class attributes and CLIP attribute text. |

## Blockers

- Find source support or mark local heuristic.
- Verify attribute tensor availability.
