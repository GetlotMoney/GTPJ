# Module Template Selection Protocol

本协议用于论文创新、用户想法或本地观察要落成 GTPJ module trial 时的模板选择。

目标不是让 agent 自由发挥，而是把创新压进少数可审查的代码框架，保证标准数据集、
标准评估和 GZSL 语义不被静默改变。

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
| 改 evaluation、split、label map 或 metric | 禁止作为普通 module trial | eval script / dataset split | 极高；不可与 baseline 直接比较 |

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

只有当机制本身不可拆分，才允许一个 Trial 使用多个模板，并标为 high risk。

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
- forward 不改变 batch 维和 class 维；
- eval 不改变 seen/unseen split、class order、label mapping、metric 语义；
- 新 loss 的 `lambda=0` 不改变 total loss；
- protected metadata 必须从 dataloader/model 读取，不手写重排。

## 阻断规则

以下情况必须阻断正式 trial：

- 缺少 `base_version` 或 `base_code_tag`。
- 缺少 `module_source.md`。
- 未选择 `template_family`。
- 模板选择理由不能解释 mechanism 到 attachment point 的映射。
- 任何代码路径会静默改变 split、class order、label mapping、logits shape 或 U/S/H/ZS 语义。
- 采样或数据视图模板没有单独高风险质量检查。
