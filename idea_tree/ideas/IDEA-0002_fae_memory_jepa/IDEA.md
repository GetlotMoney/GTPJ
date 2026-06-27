# IDEA-0002: FAE-memory JEPA auxiliary loss

```text
idea_id: IDEA-0002
title: FAE-memory JEPA auxiliary loss
status: weakened
source_type: user
source_ref: owner:2026-06-27:move AG-JEPA visual context after FAE while keeping FAE-pre patch target
source_status: local_heuristic
global_score: 72.0
idea_dir: idea_tree/ideas/IDEA-0002_fae_memory_jepa/
```

## Source

This idea came from the owner/code-review observation that the previous AG-JEPA loss used:

```text
patches -> cross_tf.embed_cv -> context/target
```

That path optimized `embed_cv`, `embed_text`, the seen text adapter path, and `jepa_predictor`, but it did not directly regularize the FAE visual memory used by the local-score path.

Long-form local note:

```text
D:/backup/Documents/Myself/GTPJ_Research/ideas/IDEA-0002_fae_memory_jepa/idea_full.md
```

## Base Version

- `v2`

## Target Component

- `model/MyModel.py`
- `CrossModalTransformer.forward`
- `GTPJ._ag_jepa_loss`
- trial-local config for `jepa_context_mode`

## Hypothesis

Use an FAE-enhanced visual context to predict a detached pre-FAE visual target:

```text
target  = mean(masked patch_z).detach()
context = mean(kept FAE memory)
text_z  = embed_text(adapted class text)
pred    = jepa_predictor([context, text_z])
loss    = 1 - cosine(pred, target)
```

The goal is to make positive JEPA loss reach `cross_tf.fae.*` while preserving class order, seen/unseen split, label mapping, logits shape, and GZSL metric semantics.

## Implementation Scope

- Add `jepa_context_mode: embed | fae_memory`.
- Keep `embed` as the baseline-off path.
- In `fae_memory` mode, align selected patches, mask, `patch_z`, FAE geometry, and context.
- Keep `target = mean(masked patch_z).detach()`.
- Keep negative JEPA visual context detached.
- Leave CLIP encoders frozen.
- Do not change scoring/eval semantics.

## Version Fit

| Version | Score | Applicability | Rationale |
|---|---:|---|---|
| `v2` | 72.0 | needs_adaptation | v2 already includes CLIP-A-self and AG-JEPA. This idea tests whether moving JEPA visual context to FAE memory improves regularization of the visual memory path. |

## Risks

- Target and context live at different representation depths.
- Patch selection alignment can silently break when `lastvit_select_k` is active.
- Strong JEPA weights may over-regularize FAE.
- Negative loss can destabilize visual memory if visual context is not detached.

## Trial Result: TRIAL-001 / ATTEMPT-001

```text
run_id: RUN-20260627-234226-trial001-fae-memory-jepa
pre_run_freeze_commit: 5ca8245e37856e426407612b1a95bcdcfbd92697
seed: 5
U/S/H/ZS: 70.32 / 77.68 / 73.82 / 81.39
best_epoch: 34
baseline_v2_H: 74.29
delta_H: -0.47
decision: revise
promotion_decision: not_applicable
```

ATTEMPT-001 proves the intended gradient path can be implemented and run cleanly, but the current parameterization underperforms active v2. This weakens the idea for v2 in its current form; it does not prove that every FAE-memory JEPA variant is invalid. Any continuation should be a targeted ATTEMPT-002 param/ablation run, not a promotion path.
