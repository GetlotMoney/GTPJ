# Architecture Change Template

只有当创新改变主模型路径或受保护的 GZSL 语义，导致它不能作为普通 module trial 处理时，
才使用本模板。

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

只要以下任一条件为 true，就把 trial 标记为 `architecture_change`：

```text
affects.forward_main_flow: true
affects.class_scoring: true
affects.train_data_view: true
affects.eval_input_output: true
affects.split_or_label_mapping: true
```

示例包括改变 forward main flow、class scoring rule、seen/unseen input contract、
training data view、evaluation input/output、prototype construction、GZSL calibration semantics、
dataloader、split 或 label mapping。

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

architecture change 仍然可能值得测试，但在 high-risk audits 通过、result records
解释清楚被改变的 contract 之前，它不能直接和普通 module trials 比较。
