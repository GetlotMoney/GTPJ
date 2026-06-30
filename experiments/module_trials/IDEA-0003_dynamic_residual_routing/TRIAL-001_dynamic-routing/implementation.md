# Implementation Record

References:

```text
docs/workflow/code_interface_contract.md
docs/workflow/innovation_code_review_protocol.md
idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
```

## New Module

`DynamicRoutingGate` is a small initialized gate used only when `use_dynamic_routing=true`.
It supports:

- `fixed`: returns a constant tensor initialized to the v5 scalar.
- `sample`: returns `[B（图片/样本数量）, 1]`.
- `class`: returns `[B（图片/样本数量）, C（类别数量）]` for score gates, or `[C_seen（seen 类数量）, 1]` for PSE.

## Based On

Base version: `v5`

Fixed anchors:

- local gate: `local_weight=0.2`
- ICSA gate: `icsa_ratio=0.008`
- direction gate: `weight_s2v=0.5`
- PSE gate: `pse_outer_ratio=0.65`

## Insertion Points

| Item | Value |
|---|---|
| File | `model/MyModel.py` |
| Class/function | `DynamicRoutingGate`, `GTPJ.forward`, `GTPJ.get_adapted_seen_text`, `GTPJ.compute_loss` |
| Before | fixed scalar routes |
| After | fixed or learned route tensors with the same broadcast target |
| Consumes | CLS/sample feature, class text, score tensors |
| Produces | dynamic gate tensors, route stats, optional anchor loss |

## Input Contract

| Name | Shape | Dtype | Device | Meaning | Gradients |
|---|---|---|---|---|---|
| `sample_feat` | `[B（图片/样本数量）, D（特征维度）]` | float | model device | CLS or normalized sample feature | yes |
| `class_text` | `[C（类别数量）, D（特征维度）]` or `[B（图片/样本数量）, C（类别数量）, D（特征维度）]` | float | model device | adapted or conditional class text | yes when text path is trainable |
| `score_s2v`, `score_v2s` | `[B（图片/样本数量）, C（类别数量）]` | float | model device | BVSA direction scores | yes |
| `pi_x` | `[B（图片/样本数量）, D（特征维度）]` | float | model device | ICSA image-conditioned text delta | yes |

## Output Contract

| Name | Shape | Meaning | Replaces Existing |
|---|---|---|---|
| `dynamic_gates.local` | `[B, 1]` or `[B, C]` | dynamic final local score weight | `local_weight` |
| `dynamic_gates.icsa` | `[B, 1]` or `[B, C_seen]` | dynamic ICSA text injection strength | `icsa_ratio` |
| `dynamic_gates.direction` | `[B, 1]` or `[B, C]` | dynamic S2V/V2S mix | `weight_s2v` |
| `dynamic_gates.pse` | `[C_seen, 1]` | dynamic PSE outer residual | `pse_outer_ratio` |
| `dynamic_route_stats.*` | scalar summary dict | mean/std/min/max/shape for logs | new |
| `dynamic_gate_anchor_loss` | scalar | unweighted gate anchor penalty | new |

## Shape Invariants

- [x] Batch dimension stays unchanged.
- [x] Class dimension stays unchanged.
- [x] Train logits stay `[B（图片/样本数量）, n_seen（训练 seen 类数量）]`.
- [x] Eval logits stay `[B（图片/样本数量）, C（全部类别数量）]`.
- [x] Visual/text embedding dimension remains 768 before existing projections.
- [x] Seen/unseen class order is unchanged.
- [x] Gate broadcasting is explicit in tests.

## Config Switches

```text
use_dynamic_routing: false
dynamic_local_mode: fixed | sample | class
dynamic_icsa_mode: fixed | sample | class
dynamic_direction_mode: fixed | sample | class
dynamic_pse_mode: fixed | class
dynamic_gate_hidden: integer
dynamic_gate_anchor_lambda: float
```

Trial base config path: `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml`

## Baseline-Off Path

`use_dynamic_routing=false` keeps the original v5 computation:

- PSE uses fixed `pse_outer_ratio`.
- ICSA uses fixed `icsa_ratio`.
- BVSA local_score uses fixed `weight_s2v`.
- final score uses fixed `local_weight`.

`dynamic_*_mode=fixed` is a switch-on sanity bridge that returns tensors equal to the fixed scalar values and is covered by tests.

## Loss Contract

```text
new loss: loss_dynamic_gate_anchor
lambda key: dynamic_gate_anchor_lambda
lambda=0 behavior: no effect on total loss
normalization/reduction changes: none
```

## Evaluation Contract

```text
eval path changed: no evaluator changes
logits shape: unchanged
class order: unchanged
metric calculation: unchanged GZSL U/S/H/ZS
```

## Checkpoint Contract

```text
new state_dict keys: dynamic_*_gate.* when use_dynamic_routing=true and mode is sample/class
old checkpoint load behavior: unchanged for use_dynamic_routing=false; strict old-checkpoint load into dynamic model may report missing dynamic gate keys
missing/unexpected keys: dynamic trial configs should not load old checkpoints with strict=True unless intentional
```

## Risks

- Gate collapse to 0 or 1.
- ICSA gate initially has no task gradient while meta_net output is zero; anchor and later meta_net movement mitigate this.
- Class-wise gates add compute and memory.
- Repeat selection can overfit a noisy single run; top2 repeats are mandatory.

## Minimum Verification

- [x] Switch-off/fixed equivalent forward pass.
- [x] Switch-on forward pass.
- [x] Logits shape check.
- [x] Loss scalar and backward check.
- [x] all_text_cond reaches BVSA local_score when configured.
- [ ] Pre-run Review 2.
- [ ] Server batch status + Result Analyst report.

## Verification Commands

```bash
python -m pytest tests/test_fae_memory_jepa.py
python -m pytest tests/test_gtpj_workflow.py -k dynamic_routing_batch_plan
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
git diff --check
```
