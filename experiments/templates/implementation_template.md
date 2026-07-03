# Implementation Record

Reference contract:

```text
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
```

Hard gate: if interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence.

## Module

```text
module_source: module_source.md
template_family: feature_adapter | fusion_gate | auxiliary_loss | sampler_or_data_view
base_version:
base_code_tag:
dataset: CUB xlsa17 att_splits
evaluation: standard GZSL U/S/H/ZS
```

## Motivation

## Attachment Point

| Item | Value |
|---|---|
| File | |
| Class/function | |
| Before/after | |
| Consumes | |
| Produces | |

## Template Selection

```text
selected_template:
selection_reason:
mechanism_claim:
why_not_narrower_template:
high_risk_reason:
```

Implementation must follow `docs/workflow/protocols/module_template_selection.md`.
If the trial changes evaluation, split, class order, label mapping, or metric semantics,
it is not a normal comparable module trial.

## Input Contract

| Name | Shape | Dtype | Device | Meaning | Gradients |
|---|---|---|---|---|---|

Shape must be written with readable meanings, for example `[B（图片/样本数量）, C（类别数量）]`; do not use unexplained dimension abbreviations.

## Output Contract

| Name | Shape | Dtype | Device | Meaning | Replaces existing variable? |
|---|---|---|---|---|---|

## Shape Invariants

- [ ] Batch dimension is unchanged.
- [ ] Class dimension is unchanged.
- [ ] Logits shape remains `[B（图片/样本数量）, C（类别数量）]`.
- [ ] Visual/text embedding dimensions remain compatible with the base scorer.
- [ ] Seen/unseen class order is unchanged.
- [ ] Label mapping is unchanged.
- [ ] No unexpected broadcasting is introduced.

## Config Switch

```text
switch:
default:
trial config path:
base config affected: no
```

## Baseline-Off Path

Explain why switching the module off is equivalent to the selected base version.

## Loss Contract

```text
new loss:
lambda key:
lambda=0 behavior:
normalization/reduction changes:
```

## Evaluation Contract

```text
eval path changed: yes/no
dataset:
split file:
logits shape:
class order:
label mapping:
seen/unseen split:
metric calculation:
metric semantics:
```

## Checkpoint Contract

```text
new state_dict keys:
old checkpoint load behavior:
missing/unexpected keys:
```

## Risk

## Minimum Verification

- [ ] Switch-off forward pass.
- [ ] Switch-on forward pass.
- [ ] Logits shape check.
- [ ] Loss scalar and backward check.
- [ ] Evaluation output class-count check.
- [ ] Label mapping check.
- [ ] Seen/unseen split check.
- [ ] Base config files did not change unexpectedly.

## Verification Command
