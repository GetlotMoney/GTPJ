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
| `standard_gzsl_module_framework_template.py` | 所有模板的公共安全框架 | protected GZSL semantics |

## 必填记录

```text
module_source_template.md
standard_trial_config_template.yaml
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
