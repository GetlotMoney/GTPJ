# Implementation Record

Reference contract:

```text
docs/workflow/code_interface_contract.md
```

Hard gate: if interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence.

## Module

## Motivation

## Attachment Point

| Item | Value |
|---|---|
| File | |
| Class/function | |
| Before/after | |
| Consumes | |
| Produces | |

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
