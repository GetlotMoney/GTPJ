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
- `sample`: returns `[B (image/sample count), 1]`.
- `class`: returns `[B (image/sample count), C (class count)]` for score gates, or `[C_seen (seen class count), 1]` for PSE.

## Based On

Base version: `v5`

Fixed anchors:

- local gate: `local_weight=0.2`
- ICSA gate: `icsa_ratio=0.008`
- direction gate: `weight_s2v=0.5`
- PSE gate: `pse_outer_ratio=0.65`

## Insertion Points

| Gate | File/function | Before | After | First-principles intent |
|---|---|---|---|---|
| `local_gate` | `model/MyModel.py`, final score blend | fixed `local_weight` | fixed/sample/class gate tensor | add more local evidence when the sample/class pair needs fine-grained part evidence; add less when local evidence overfits seen classes |
| `icsa_gate` | `GTPJ.forward`, ICSA text injection | fixed `icsa_ratio` | fixed/sample/class gate tensor | control image-conditioned text perturbation strength; this proved unstable in ATTEMPT-001 |
| `direction_gate` | BVSA direction mix | fixed `weight_s2v` | fixed/sample/class gate tensor | choose S2V vs V2S mixture per sample/class according to alignment direction reliability |
| `pse_gate` | `get_adapted_seen_text`, PSE outer residual | fixed `pse_outer_ratio` | fixed/class gate tensor | preserve raw text when PSE adaptation risks drift; trust PSE more for classes whose seen prototypes benefit from adaptation |

## Input Contract

| Name | Shape | Dtype | Device | Meaning | Gradients |
|---|---|---|---|---|---|
| `sample_feat` | `[B (image/sample count), D (feature dimension)]` | float | model device | CLS or normalized sample feature | yes |
| `class_text` | `[C (class count), D (feature dimension)]` or `[B (image/sample count), C (class count), D (feature dimension)]` | float | model device | adapted or conditional class text | yes when text path is trainable |
| `score_s2v`, `score_v2s` | `[B (image/sample count), C (class count)]` | float | model device | BVSA direction scores | yes |
| `pi_x` | `[B (image/sample count), D (feature dimension)]` | float | model device | ICSA image-conditioned text delta | yes |

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
- [x] Train logits stay `[B (image/sample count), n_seen (training seen class count)]`.
- [x] Eval logits stay `[B (image/sample count), C (all class count)]`.
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

## Batch Profiles

Implemented workflow profiles:

- `balanced-aggressive`: first 50-job batch; completed as `RUN-20260630-0005-dynroute50-2gpu`.
- `principled-followup`: second 50-job design after ATTEMPT-001; keeps ICSA fixed, explores direction/local/PSE more deliberately, and repeats top 3.

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
old checkpoint load behavior: unchanged for use_dynamic_routing=false
strict old-checkpoint load into a dynamic model may report missing dynamic gate keys
```

## ATTEMPT-001 Runtime Outcome

The first batch did not promote dynamic routing:

- best overall: DR-001 static control, H=74.40;
- best dynamic single: DR-008 local_class_h24, H=74.39;
- best dynamic repeat mean: DR-008, H=74.23;
- best direction single: DR-023, H=74.38 with U=72.26;
- dynamic ICSA and combinations were unstable.

## Risks

- Gate collapse to 0 or 1.
- ICSA gate can over-inject unstable image-conditioned text.
- Class-wise gates add compute and memory.
- Repeat selection can overfit a noisy single run; repeat means are mandatory.

## Verification Commands

```bash
python -m pytest tests/test_fae_memory_jepa.py
python -m pytest tests/test_gtpj_workflow.py -q -k dynamic_routing
python -m py_compile model/MyModel.py workflow/gtpj_workflow.py train_GTPJ_CUB.py
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
git diff --check
```
