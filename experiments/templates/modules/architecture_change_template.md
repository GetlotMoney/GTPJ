# Architecture Change Template

Use this only when an innovation changes the main model path or protected GZSL
semantics enough that it cannot be treated as a normal module trial.

```text
module_scope: architecture_change
template_family: architecture_change
risk: high
base_version:
base_code_tag:
dataset: CUB xlsa17 att_splits
evaluation: standard GZSL U/S/H/ZS
```

## Trigger

Mark the trial as `architecture_change` when any of these are true:

```text
affects.forward_main_flow: true
affects.class_scoring: true
affects.train_data_view: true
affects.eval_input_output: true
affects.split_or_label_mapping: true
```

Examples include changing the forward main flow, class scoring rule, seen/unseen
input contract, training data view, evaluation input/output, prototype
construction, GZSL calibration semantics, dataloader, split, or label mapping.

## Required Audits

```text
interface_precheck: required
switch_off_equivalence: required
shape_audit: required
standard_gzsl_eval_audit: required
split_integrity_audit: required
class_order_audit: required
```

## Boundary

An architecture change may still be worth testing, but it is not directly
comparable with normal module trials until the high-risk audits pass and the
result records explain the changed contract.
