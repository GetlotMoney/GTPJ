# Implementation Record

参考 contract：

```text
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
```

硬门：如果 interface、label mapping、seen/unseen split、class order、logits shape
或 metric semantics 不清楚，该实验就是无效证据。

## Module

```text
module_source: module_source.md
trial_meta: trial_meta.yaml
template_family: feature_adapter | fusion_gate | auxiliary_loss | sampler_or_data_view | composite
module_scope: single_module | composite | architecture_change
training_template: experiments/templates/modules/standard_gzsl_training_template.py
training_entry_mode: existing_entry_equivalent | strict_template_entry
selected_training_entry:
legacy_module_migration: not_required | required | completed
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

实现必须遵守 `docs/workflow/protocols/module_template_selection.md`。如果 trial 改变
evaluation、split、class order、label mapping 或 metric semantics，它就不是普通可比较的
module trial。

## Training Entry

```text
selected_training_entry:
training_entry_mode:
standard_template: experiments/templates/modules/standard_gzsl_training_template.py
strict_template_rule:
legacy_module_migration:
equivalence_note:
config_path:
seed:
dataset_loader:
eval_function:
checkpoint_policy:
artifact_refs:
```

说明本次 run 使用复制出的训练模板，还是使用类似 `train_GTPJ_CUB.py` 的既有入口。
说明必须映射 config、seed、dataset/split、frozen backbone、model/module、train loop、
standard GZSL eval、checkpoint/log retention，以及 result/quality summaries。
如果 `training_entry_mode: strict_template_entry`，Runner 必须使用从
`standard_gzsl_training_template.py` 复制出的 trial-local training entry。旧入口中已经打开的
任何模块都必须迁移到这个干净入口里；不要继续往旧训练脚本堆分支。

## Input Contract

| Name | Shape | Dtype | Device | Meaning | Gradients |
|---|---|---|---|---|---|

Shape must be written with readable meanings, for example `[B（图片/样本数量）, C（类别数量）]`; do not use unexplained dimension abbreviations.

## Output Contract

| Name | Shape | Dtype | Device | Meaning | Replaces existing variable? |
|---|---|---|---|---|---|

## Shape Invariants

- [ ] Batch dimension 不变。
- [ ] Class dimension 不变。
- [ ] Logits shape remains `[B（图片/样本数量）, C（类别数量）]`.
- [ ] Visual/text embedding dimensions 仍然兼容 base scorer。
- [ ] Seen/unseen class order 不变。
- [ ] Label mapping 不变。
- [ ] 没有引入意外 broadcasting。

## Config Switch

```text
switch:
default:
trial config path:
base config affected: no
```

## Baseline-Off Path

说明为什么关闭该模块后等价于选定的 base version。

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

- [ ] Switch-off forward pass。
- [ ] Switch-on forward pass。
- [ ] Logits shape check。
- [ ] Loss scalar 和 backward check。
- [ ] Evaluation output class-count check。
- [ ] Label mapping check。
- [ ] Seen/unseen split check。
- [ ] Base config files 没有意外变化。

## Verification Command
