# IDEA-0005: Counterfactual negative text margin

```text
idea_id: IDEA-0005
status: candidate
source_type: observation
source_status: unknown
global_score: 40
current_version_score:
  v1: 40
idea_dir: idea_tree/ideas/IDEA-0005_counterfactual_negative_text/
```

## Source

Source unclear. Migrated from inactive `use_cf_neg_text` switch.

## Based On

- `v1`
- GPT text prototypes
- base logits

## Hypothesis

Mining text-neighbor negative classes and enforcing a margin may reduce confusion between semantically similar seen classes.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 40 | direct | Can be tested as an auxiliary margin without changing logits shape. |

## Blockers

- Record source or local-heuristic rationale.
- Guard against seen over-separation.
