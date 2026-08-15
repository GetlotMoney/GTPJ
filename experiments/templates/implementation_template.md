# Implementation Record（实现记录）

参考 contract：

```text
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
```

硬门：如果 interface、label mapping、seen/unseen split、class order、logits shape
或 metric semantics 不清楚，该实验就是无效证据。

## Module（模块）

```text
module_abbreviation:
module_full_name_en:
module_name_zh:
module_plain_purpose:  # 一句话说明它解决什么问题、做什么
```

第一次解释模块时必须同时填写英文缩写、英文全称、中文含义和一句话作用，不能只写缩写。

本文件只用于产生或改变方法框架的代码模块变动。调参、复现、只关闭既有组件的窄消融不需要新增本文件；
如果一次实验要新增或改写 module、forward、loss、evaluation、data view、接口语义或模块分支逻辑，
它应被路由为 innovation / module trial。

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

## Motivation（动机）

## Attachment Point（接入点）

| 项目 | 值 |
|---|---|
| 文件 | |
| 类 / 函数 | |
| 接入前后位置 | |
| 读取内容 | |
| 产出内容 | |

## Template Selection（模板选择）

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

## Training Entry（训练入口）

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

## Input Contract（输入契约）

| 名称 | Shape（形状） | Dtype（数据类型） | Device（设备） | 含义 | Gradients（梯度） |
|---|---|---|---|---|---|

Shape 必须写出可读含义，例如 `[B（图片/样本数量）, C（类别数量）]`；不要使用未解释的维度缩写。

## Output Contract（输出契约）

| 名称 | Shape（形状） | Dtype（数据类型） | Device（设备） | 含义 | 是否替换已有变量 |
|---|---|---|---|---|---|

## Shape Invariants（形状不变量）

- [ ] Batch dimension 不变。
- [ ] Class dimension 不变。
- [ ] Logits shape 保持为 `[B（图片/样本数量）, C（类别数量）]`。
- [ ] Visual/text embedding dimensions 仍然兼容 base scorer。
- [ ] Seen/unseen class order 不变。
- [ ] Label mapping 不变。
- [ ] 没有引入意外 broadcasting。

## Config Switch（配置开关）

```text
switch:
default:
trial config path:
base config affected: no
```

## Baseline-Off Path（关闭模块后的基线路径）

说明为什么关闭该模块后等价于选定的 base version。

## Loss Contract（损失契约）

```text
new loss:
lambda key:
lambda=0 behavior:
normalization/reduction changes:
```

## Evaluation Contract（评估契约）

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

## Checkpoint Contract（Checkpoint 契约）

```text
new state_dict keys:
old checkpoint load behavior:
missing/unexpected keys:
```

## Risk（风险）

## Minimum Verification（最低验证）

- [ ] Switch-off forward pass。
- [ ] Switch-on forward pass。
- [ ] Logits shape check。
- [ ] Loss scalar 和 backward check。
- [ ] Evaluation output class-count check。
- [ ] Label mapping check。
- [ ] Seen/unseen split check。
- [ ] Base config files 没有意外变化。

## Verification Command（验证命令）
