# Module Template Selection Protocol

本协议用于论文创新、用户想法或本地观察要落成 GTPJ module trial 时的模板选择。

目标不是让 agent 自由发挥，而是把创新压进少数可审查的代码框架，保证标准数据集、
标准评估和 GZSL 语义不被静默改变。

工程原则：

```text
创新内部可以复杂，但主训练框架只能感知一个标准 trial 插槽。
```

## 硬前置

正式 module trial 必须先明确：

```text
base_version: vX
base_code_tag: vX
dataset: CUB xlsa17 att_splits
evaluation: standard GZSL U/S/H/ZS
```

如果 owner 只说“从论文开始”但没有指定 `base_version`，只能做 paper intake / idea discovery，
不得创建 trial、改代码或启动 Runner。

## 模板选择顺序

按下面顺序选择最窄模板。能用窄模板时，不升级成宽模板。

| 机制意图 | 默认模板 | 典型接入点 | GZSL 风险 |
|---|---|---|---|
| 改 visual/text/class feature 表示 | `feature_adapter_template.py` | feature encoder 后、scorer 前 | 中 |
| 改多路分数或特征融合 | `fusion_gate_template.py` | global/local score 或 text/visual branch 融合处 | 中 |
| 只新增正则或辅助 loss | `auxiliary_loss_template.py` | `compute_loss` 内，读取已有 tensor | 中低 |
| 改采样、cache view、patch/view 选择 | `sampler_or_data_view_template.py` | batch / feature cache / view selector | 高 |
| 两个或更多模块必须一起才构成机制 | `composite_module_template.py` | 一个 composite slot 统一调 feature/fusion/loss/view 子模块 | 高 |
| 改 forward、class scoring、data view、evaluation、split、label map 或 metric | `architecture_change_template.md` | 单独高风险主干流程 | 极高；不可与普通 trial 直接比较 |

选择算法：

```text
paper mechanism
-> 写 mechanism claim
-> 找 attachment point
-> 判断是否触碰 protected GZSL semantics
-> 选择最窄模板
-> 写 module_source.md
-> 写 implementation.md
-> Review 0/1
-> 实现
```

如果一个 idea 同时需要多个模板，默认拆成多个 Trial：

```text
TRIAL-001: feature adapter
TRIAL-002: auxiliary loss
TRIAL-003: fusion gate
```

只有当机制本身不可拆分，才允许一个 Trial 使用多个模板，并必须走
`composite_module_template.py`。主训练框架只能看到一个 composite 插槽，不能在
`train_GTPJ_CUB.py` 或旧模型里散落多处临时分支。composite trial 必须记录：

```text
module_scope: composite
components:
  - name:
    template_family:
    attachment_point:
    enabled_key:
composition_mode: sequential | parallel | gated | residual
baseline_off_explanation:
```

如果两个子模块可以独立验证，仍然拆成多个 Trial；只有一起才成立的机制才用 composite。

## Trial Meta 分流

每个正式 Trial 必须有 trial-local `trial_meta.yaml`，从
`trial_meta_template.yaml` 复制，至少记录：

```yaml
module_scope: single_module | composite | architecture_change
template_family: feature_adapter | fusion_gate | auxiliary_loss | sampler_or_data_view | composite | architecture_change
affects:
  forward_main_flow: false
  class_scoring: false
  train_data_view: false
  eval_input_output: false
  split_or_label_mapping: false
baseline_off:
  supported: true
audit:
  shape_audit: required
  switch_off_equivalence: required
  standard_gzsl_eval_audit: required
```

判定逻辑：

```text
一个创新点能拆开验证 -> 拆成多个 single_module trials
两个模块必须一起才有意义 -> composite trial
只要影响主流程、class scoring、eval、split -> architecture_change trial
```

如果 `module_scope: single_module` 或 `module_scope: composite` 但 `affects.*`
任一高风险项为 true，必须升级为 `module_scope: architecture_change`。

## 标准 GZSL 边界

任何模板都必须保护：

```text
dataset: CUB xlsa17 split by default
train classes: seen only
test classes: seen + unseen
label mapping: unchanged
class order: unchanged
seen/unseen split: unchanged
logits: [B（图片/样本数量）, C（类别数量）]
metrics: U, S, H, ZS
```

如果实验要支持 AWA2/SUN，必须显式记录 dataset_name、split file、class count 和 label map，
并证明其评估仍是标准 GZSL。不能把跨数据集适配混进同一个 CUB module trial。

## Module Source 解释

每个新模块必须有 trial-local `module_source.md`，至少记录：

```text
source_type:
paper_id:
source_ref:
official_code_url:
official_code_path:
mechanism_claim:
what_is_copied:
what_is_adapted:
what_is_new:
why_fit_gtpj:
template_family:
attachment_point:
paper_to_code_mapping:
baseline_off_explanation:
paper_writing_note:
```

旧 baseline 可以没有来源追溯；新 module trial 不允许缺失。

## 标准代码框架

所有模板必须继承或复制 `standard_gzsl_module_framework_template.py` 的保护思想：

- config switch 默认关闭；
- switch off 等价于 `base_version`；
- composite trial 的 all components off 等价于 `base_version`；
- forward 不改变 batch 维和 class 维；
- eval 不改变 seen/unseen split、class order、label mapping、metric 语义；
- 新 loss 的 `lambda=0` 不改变 total loss；
- protected metadata 必须从 dataloader/model 读取，不手写重排。

## 标准训练入口

正式 module trial 还必须继承或对照
`standard_gzsl_training_template.py` 的完整训练入口结构：

```text
config -> seed -> dataset/split -> frozen backbone -> model/module -> train loop -> standard GZSL eval -> checkpoint/artifact refs -> result/quality summary
```

训练入口有两种模式，必须写入 `trial_meta.yaml` 的 `training_entry.mode`：

```text
existing_entry_equivalent
strict_template_entry
```

默认模式是 `existing_entry_equivalent`：已有 `train_GTPJ_CUB.py` 可以作为等价实现继续使用，
但 trial-local `implementation.md` 必须说明它与训练模板的对应关系。

如果 owner 明确说“用新模板”“用新的训练模板”“不要继承老模板”，必须使用
`strict_template_entry`。此时 Runner 只能使用从
`standard_gzsl_training_template.py` 复制出的 trial-local `training_entry.py`，不能继续在
`train_GTPJ_CUB.py` 或旧训练入口里追加分支。旧入口中本次实验需要打开的模块必须迁移到
`training_entry.py`，并记录：

```text
training_entry_mode: strict_template_entry
selected_training_entry: training_entry.py
legacy_module_migration: required | completed
```

新训练入口不得跳过：

- `base_version` / `base_code_tag`；
- `module_source.md`；
- `trial_meta.yaml`；
- `module_template_family`；
- CUB xlsa17 split 或显式 high-risk dataset adaptation note；
- standard GZSL U/S/H/ZS evaluation；
- `best_H` 只作为 observed result，不能自动写成 confirmed；
- checkpoint / log / result artifact refs。

这些模板只在 GTPJ 标准 GZSL module trial 范围内通用。若改成 AWA2/SUN、
非 xlsa17 split、非 GZSL 任务或新评估指标，必须单独记录适配边界，不能直接与
CUB xlsa17 baseline 互相比。

## 阻断规则

以下情况必须阻断正式 trial：

- 缺少 `base_version` 或 `base_code_tag`。
- 缺少 `module_source.md`。
- 缺少 `trial_meta.yaml` 或 `validate-trial-meta` 不通过。
- 未选择 `template_family`。
- 缺少 `standard_gzsl_training_template.py` 对照或等价训练入口说明。
- owner 已要求新模板，但 `training_entry.mode` 不是 `strict_template_entry`。
- `strict_template_entry` 仍选择 `train_GTPJ_CUB.py` 或没有迁移旧入口中已打开模块。
- 模板选择理由不能解释 mechanism 到 attachment point 的映射。
- 任何代码路径会静默改变 split、class order、label mapping、logits shape 或 U/S/H/ZS 语义。
- 采样或数据视图模板没有单独高风险质量检查。
