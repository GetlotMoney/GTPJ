# IDEA-0009: Uncertainty-aware MSDN gate

```text
idea_id: IDEA-0009
status: candidate
source_type: observation
source_status: unknown
global_score: 50
current_version_score:
  v1: 50
idea_dir: idea_tree/ideas/IDEA-0009_uncertainty_msdn_gate/
```

## Source

Source unclear. Migrated from inactive `use_uncertainty_msdn_gate` switch.

## Based On

- `v1`
- MSDN mutual branch distillation
- score_s2v
- score_v2s

## Hypothesis

Reducing mutual distillation weight when branches are uncertain or disagree may prevent wrong consensus from being reinforced.

## Version Scores

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v1` | 50 | direct | v1 actively uses MSDN and logits shape is unchanged. |

## Blockers

- Document confidence-gating source or local rationale.
- Check whether gating weakens active distillation.
