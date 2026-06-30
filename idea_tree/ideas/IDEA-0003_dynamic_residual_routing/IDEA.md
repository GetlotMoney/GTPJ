# IDEA-0003: Dynamic Residual Routing

```text
idea_id: IDEA-0003
title: Dynamic Residual Routing
status: selected
source_type: user
source_ref: owner:2026-06-30:make residual and mixture coefficients dynamic routes
source_status: local_heuristic
global_score: 78.0
idea_dir: idea_tree/ideas/IDEA-0003_dynamic_residual_routing/
base_version: v5
```

## Source

Owner hypothesis: several current GTPJ paths behave like fixed residual or mixture routes, for example `a*x + (1-a)*x` or `S_global + local_weight * S_local`.
This idea tests whether those fixed coefficients should become learned dynamic gates rather than one global constant.

## Based On

- `GTPJ-v5` active mainline.
- Current fixed routing coefficients:
  - `local_weight`
  - `icsa_ratio`
  - `weight_s2v`
  - `pse_outer_ratio`
- Existing modules: PSE, ICSA, BVSA local score, BVSA direction mix, FGVD, SGMP.

## Target Component

`model/MyModel.py` dynamic residual and score routing.

## Hypothesis

Replacing v5 fixed coefficients with gates initialized near the fixed values can adapt local score strength, ICSA injection strength, BVSA direction mix, and PSE outer residual per sample or class.
If the gates avoid collapse, they may preserve seen-class strength while improving unseen transfer and H stability.

## Implementation Scope

TRIAL-001 only adds:

- Dynamic gate modules for local, ICSA, direction, and PSE outer routing.
- Config switches and gate modes.
- Gate statistics in forward outputs and training logs.
- Tests for shape, switch-off behavior, conditional BVSA text, and gradient reachability.
- Workflow helpers for a balanced-aggressive 50-job two-GPU batch.

TRIAL-001 must not change dataset split, class order, label mapping, logits shape, metric semantics, optimizer, or promotion status.

## Expected Effect

| Metric | Expectation |
|---|---|
| U | Main target. Dynamic local/ICSA/PSE balance may improve unseen transfer by avoiding a single fixed seen-biased coefficient. |
| S | Should stay near v5 if gates initialize around v5 fixed values and anchor regularization is enabled. |
| H | Target improvement is repeat mean above v5 repeat mean H=74.44 and preferably above v4 confirmed_H=74.45. |

## Version Adaptation

| Version | Score | Applicability | Stage | Rationale |
|---|---:|---|---|---|
| `v5` | 82.0 | direct | selected | v5 already routes `all_text_cond` into BVSA when configured, and has the fixed residual/mix coefficients this trial will replace dynamically. |

## Compatibility

- `use_dynamic_routing=false` keeps the v5 fixed path.
- `dynamic_*_mode=fixed` initializes gates to the corresponding v5 scalar values.
- New gates are trial-local until the result is promoted.

## Risks

- Gate collapse to 0 or 1.
- Hidden seen-class overfit.
- Sample/class broadcasting mistakes.
- Silent drift in switch-off behavior.
- Config alias drift between framework names and legacy keys.
- Extra compute or memory from class-wise gates.

## Decision Rule

This idea can only move beyond trial evidence if:

- 50-run batch has complete status and failure accounting.
- Top2 frozen repeats complete.
- Repeat mean clearly beats v5 repeat mean H=74.44 and is compared against v4 confirmed_H=74.45.
- Interface and quality checks confirm class order, seen/unseen split, logits shape, and metric semantics are unchanged.

## Next Action

Create `TRIAL-001_dynamic-routing`, implement the trial-local dynamic routing code path, freeze the experiment branch, and run the balanced-aggressive 50-job server batch.
