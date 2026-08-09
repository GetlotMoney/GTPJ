# 模块代码模板

这些模板用于新 module trial 的实现骨架。它们不是当前 baseline 代码，不能直接当作结果证据。
使用时复制到 trial 分支，按 `module_source.md` 和 `implementation.md` 填写，再经过 Review 0-3。

## 选择表

| 模板 | 适用场景 | 不允许改变 |
|---|---|---|
| `feature_adapter_template.py` | 论文想法改变 visual/text/class feature 表示 | split、label map、class order、logits shape |
| `fusion_gate_template.py` | 论文想法改变多路 score/feature 融合 | eval metric、class axis、baseline-off path |
| `auxiliary_loss_template.py` | 论文想法只新增辅助监督或正则项 | `lambda=0` 时 total loss 行为 |
| `sampler_or_data_view_template.py` | 论文想法改变采样、cache view 或 patch/view 选择 | xlsa17 split、labels、eval loader |
| `composite_module_template.py` | 论文想法必须融合两个或更多模块才成立 | 主训练框架只能看到一个 composite slot；所有子模块关闭后回到 baseline |
| `architecture_change_template.md` | 论文想法触碰 forward/scoring/eval/split 主干语义 | 必须走高风险 architecture audit |
| `standard_gzsl_module_framework_template.py` | 所有模板的公共安全框架 | 受保护的 GZSL 语义 |

## 必填记录

```text
module_source_template.md
trial_meta_template.yaml
standard_trial_config_template.yaml
standard_gzsl_training_template.py
composite_module_template.py (only for inseparable multi-component trials)
architecture_change_template.md (only for high-risk architecture trials)
implementation.md
interface_precheck.md
quality_check.md
```

每个模板都必须保持：

```text
logits: [B（图片/样本数量）, C（类别数量）]
metrics: U, S, H, ZS
dataset default: CUB xlsa17 att_splits
```

`standard_gzsl_training_template.py` 是正式 module trial 的完整训练入口脚手架。
其它文件是模块级模板。它们整体可复用于 GTPJ 标准 GZSL trial，但不是适用于所有
model、dataset、split 或 evaluation protocol 的通用模板。

训练入口模式：

```text
existing_entry_equivalent: 允许使用既有 train_GTPJ_CUB.py，但 implementation.md 必须说明它如何等价映射到标准训练模板。
strict_template_entry: Runner 必须使用从标准模板复制出的 trial-local training_entry.py。
```

只要 owner 明确说使用新模板，就使用 `strict_template_entry`。在这种模式下，
旧入口里已经打开的模块必须迁移到 trial-local clean entry，不要继续往旧脚本加分支。

工程规则：

```text
创新内部可以复杂，但主训练框架只能看到一个标准 trial slot。
```
