# Implementation Record: FAE-memory JEPA

参考契约：

```text
docs/workflow/code_interface_contract.md
docs/workflow/innovation_code_review_protocol.md
```

## 新模块

FAE-memory JEPA auxiliary-loss mode.

## 基于什么

- GTPJ-v2 active code.
- Existing AG-JEPA loss in `GTPJ._ag_jepa_loss`.
- Existing FAE path in `CrossModalTransformer.forward`.

## 接入点

| 项目 | 值 |
|---|---|
| File | `model/MyModel.py` |
| Class/function | `CrossModalTransformer.forward`, `GTPJ.forward`, `GTPJ._ag_jepa_loss` |
| 接入前/后 | After selected patches are projected by `embed_cv`; before JEPA predictor |
| Consumes | selected patches, selected indices, `patch_z`, adapted class text |
| Produces | auxiliary JEPA context/target tensors and scalar losses |

## Input Contract（输入契约）

| 名称 | Shape | Dtype | Device | 含义 | Gradients |
|---|---|---|---|---|---|
| selected_patches | `[B（图片/样本数量）, K_sel（选中 patch 数）, 768（CLIP 视觉维度）]` | float | cuda/cpu | LaSt-ViT 后的 visual patch set | no upstream CLIP grad |
| patch_z | `[B, K_sel, 512]` | float | cuda/cpu | FAE 前 visual projection | yes, through context path |
| keep_fae_context | `[B, 512]` | float | cuda/cpu | keep-only FAE visual memory pooled context | yes |
| class_text | `[B, 768]` | float | cuda/cpu | CLIP-A-self adapted seen class text | yes for adapter path |
| text_z | `[B, 512]` | float | cuda/cpu | projected semantic condition | yes |

## Output Contract（输出契约）

| 名称 | Shape | Dtype | Device | 含义 | 是否替换已有变量 |
|---|---|---|---|---|---|
| loss_jepa | scalar | float | cuda/cpu | positive JEPA cosine loss | no |
| loss_jepa_neg | scalar | float | cuda/cpu | negative margin loss | no |
| logits/logits_200 | unchanged | float | cuda/cpu | GZSL logits | no |

## Shape Invariants（形状不变量）

- [x] Batch dimension 保持不变。
- [x] Class dimension 保持不变。
- [x] Logits shape 保持 `[B（图片/样本数量）, C（类别数量）]`。
- [x] Visual/text embedding dimensions 仍与 scorer 兼容。
- [x] Seen/unseen 类别顺序不变。
- [x] 没有引入意外 broadcasting。

## 配置开关

```text
switch: jepa_context_mode
default: embed
trial config path: attempts/ATTEMPT-001/config.yaml
base config affected: no
```

## Baseline-Off Path（基线关闭路径）

`jepa_context_mode: embed` keeps the current AG-JEPA implementation: `context` and `target`
are both computed from `cross_tf.embed_cv(patches)` before FAE. Existing configs that do not
define `jepa_context_mode` default to `embed`.

## Loss Contract（Loss 契约）

```text
new loss: no new loss name; existing AG-JEPA loss gets a new context mode
lambda key: lambda_jepa, lambda_jepa_neg
lambda=0 behavior: JEPA contributes nothing to total loss
normalization/reduction changes: none; existing mean reduction is preserved
```

## Evaluation Contract（评估契约）

```text
eval path changed: no
logits shape: unchanged
class order: unchanged 0..199
metric calculation: unchanged GZSL U/S/H/ZS
```

## Checkpoint Contract（Checkpoint 契约）

```text
new state_dict keys: none expected
old checkpoint load behavior: unchanged, unless future code adds explicit parameters
missing/unexpected keys: none expected
```

## 风险

- FAE context must be computed from keep tokens only to avoid target leakage through FAE self-attention.
- selected patch alignment must be shared by mask, target, and context.
- Negative branch should detach visual context.
- `fae_memory` mode must reject `use_fae: false`.

## Minimum Verification（最低验证）

- [ ] Switch-off forward pass。
- [ ] Switch-on forward pass。
- [ ] Logits shape check。
- [ ] Loss scalar 和 backward check。
- [ ] FAE gradient probe。
- [ ] Evaluation 输出 class-count 检查。
- [ ] Base config files 没有变化。

## 验证命令

```powershell
python -m py_compile model/MyModel.py
python -m unittest tests.test_gtpj_workflow
python -m unittest tests.test_fae_memory_jepa
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
git diff --check
```
