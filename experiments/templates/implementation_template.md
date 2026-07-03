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
trial_meta: trial_meta.yaml
template_family: feature_adapter | fusion_gate | auxiliary_loss | sampler_or_data_view | composite
module_scope: single_module | composite | architecture_change
training_template: experiments/templates/modules/standard_gzsl_training_template.py
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
module_scope:
components:
composition_mode:
affects:
  forward_main_flow:
  class_scoring:
  train_data_view:
  eval_input_output:
  split_or_label_mapping:
high_risk_reason:
```

Implementation must follow `docs/workflow/protocols/module_template_selection.md`.
If the trial changes evaluation, split, class order, label mapping, or metric semantics,
it is not a normal comparable module trial.

## Training Entry

```text
selected_training_entry:
standard_template: experiments/templates/modules/standard_gzsl_training_template.py
equivalence_note:
config_path:
seed:
dataset_loader:
eval_function:
checkpoint_policy:
artifact_refs:
```

Explain whether the run uses a copied training template or an existing entry
such as `train_GTPJ_CUB.py`. The explanation must map config, seed,
dataset/split, frozen backbone, model/module, train loop, standard GZSL eval,
checkpoint/log retention, and result/quality summaries.

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
