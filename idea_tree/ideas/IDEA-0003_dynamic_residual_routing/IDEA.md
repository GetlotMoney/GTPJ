# IDEA-0003: Dynamic Residual Routing

```text
idea_id: IDEA-0003
title: Dynamic Residual Routing
status: weakened
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
| H | 目标是让重复均值超过 v5 repeat mean H=74.44，并与 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47 比较。 |

## Version Adaptation

| Version | Score | Applicability | Stage | Rationale |
|---|---:|---|---|---|
| `v5` | 82.0 | direct | trialing | v5 already routes `all_text_cond` into BVSA when configured, and has the fixed residual/mix coefficients this trial will replace dynamically. |

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
- 重复均值明确超过 v5 repeat mean H=74.44，并与 v3/CONFIRM-001 local-v3-054 confirmed_H=74.47 比较。
- Interface and quality checks confirm class order, seen/unseen split, logits shape, and metric semantics are unchanged.

## 当前实验结果

TRIAL-001 已记录到 ATTEMPT-018。当前研究前沿如下：

- ATTEMPT-017 `DR-095 / a015dr035_weight_plus_0.01` 为最高单次，`H=75.11`、`U=73.00`、`S=77.36`、`ZS=82.12`。
- ATTEMPT-015 的 100 jobs 中有 15 个 `H>=74.80`，其中 `75.04/75.00` 两个达到 75；ATTEMPT-011 也选出了 12 个 `H>=74.80` 来源候选。
- ATTEMPT-018 对 `H=75.11` 候选完成 5 次同配置、同 seed exact repeat，最好 `H=74.71`、均值 `H=74.58`，未还原。
- ATTEMPT-014 的 exact repeat 曾达到 `H=74.99`，但它还原的是来源目标 `74.89`，不能解释为 75 已复现。
- 正式 confirmed reference 仍是 `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47`。

结论：动态路由在 direction_sample h48 小 anchor 区域具有连续高分信号，但 75+ 来源候选尚未稳定复现。保留该 idea 为 `weakened/trialing`，`promotion_decision: blocked`。

## Next Action

不要继续追加 ATTEMPT-017 `DR-095` 的复现次数；它已经达到 5 次 hard cap。后续如继续研究，应基于 `74.8x/74.9x` 密集带提出新的机制假设或新候选，再走独立的 tune -> exact repeat 证据链。
