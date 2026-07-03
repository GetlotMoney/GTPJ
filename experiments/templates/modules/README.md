# Module Code Templates

这些模板用于新 module trial 的实现骨架。它们不是当前 baseline 代码，不能直接当作结果证据。
使用时复制到 trial 分支，按 `module_source.md` 和 `implementation.md` 填写，再经过 Review 0-3。

## 选择表

| Template | Use when | Must not change |
|---|---|---|
| `feature_adapter_template.py` | paper idea 改 visual/text/class feature 表示 | split, label map, class order, logits shape |
| `fusion_gate_template.py` | paper idea 改多路 score/feature 融合 | eval metric, class axis, baseline-off path |
| `auxiliary_loss_template.py` | paper idea 只新增辅助监督或正则 | total loss when lambda=0 |
| `sampler_or_data_view_template.py` | paper idea 改采样、cache view 或 patch/view 选择 | xlsa17 split, labels, eval loader |
| `composite_module_template.py` | paper idea 必须融合两个或更多模块才成立 | one composite slot, all-off baseline path |
| `architecture_change_template.md` | paper idea 触碰 forward/scoring/eval/split 主干语义 | high-risk architecture audit |
| `standard_gzsl_module_framework_template.py` | 所有模板的公共安全框架 | protected GZSL semantics |

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

`standard_gzsl_training_template.py` is the full training-entry scaffold for
formal module trials. The other files are module-level templates. Together they
are reusable for GTPJ standard GZSL trials, but they are not universal templates
for every model, dataset, split, or evaluation protocol.

Engineering rule:

```text
Innovation may be complex internally, but the main training framework may only
see one standard trial slot.
```
