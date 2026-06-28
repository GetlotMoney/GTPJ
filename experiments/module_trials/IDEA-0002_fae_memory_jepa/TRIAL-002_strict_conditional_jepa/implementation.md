# Implementation Record: FAE-memory JEPA

References:

```text
docs/workflow/code_interface_contract.md
docs/workflow/innovation_code_review_protocol.md
```

## Module

Strict main-path FAE-memory JEPA auxiliary-loss mode with conditional AG-JEPA text.

## Base

- GTPJ-v2 active code.
- Existing AG-JEPA loss in `GTPJ._ag_jepa_loss`.
- Existing FAE path in `CrossModalTransformer.forward`.

## Insertion Point

| Item | Value |
|---|---|
| File | `model/MyModel.py` |
| Class/function | `CrossModalTransformer.forward`, `GTPJ.forward`, `GTPJ._ag_jepa_loss` |
| Position | After selected patches are projected by `embed_cv`; before JEPA predictor |
| Consumes | Selected patches, selected indices, `patch_z`, adapted class text |
| Produces | Auxiliary JEPA context/target tensors and scalar losses |

## Input Contract

| Name | Shape | Dtype | Device | Meaning | Gradients |
|---|---|---|---|---|---|
| `selected_patches` | `[B (images), K_sel (selected patches), 768 (CLIP visual dim)]` | float | cuda/cpu | LaSt-ViT selected visual patch set | no upstream CLIP grad |
| `patch_z` | `[B, K_sel, 512]` | float | cuda/cpu | pre-FAE visual projection | yes through context path |
| `jepa_memory` | `[B, K_sel, 512]` | float | cuda/cpu | main forward path FAE memory used by local score | yes |
| `class_text` | `[B, 768]` | float | cuda/cpu | CLIP-A-self adapted seen class text | yes for adapter path |
| `all_text_cond[b, label]` | `[B, 768]` | float | cuda/cpu | sample-conditioned class text from `meta_net(cls_token)` | yes for `meta_net` and text projection |
| `text_z` | `[B, 512]` | float | cuda/cpu | projected semantic condition | yes |

## Output Contract

| Name | Shape | Dtype | Device | Meaning | Replaces existing variable |
|---|---|---|---|---|---|
| `loss_jepa` | scalar | float | cuda/cpu | positive JEPA cosine loss | no |
| `loss_jepa_neg` | scalar | float | cuda/cpu | negative margin loss | no |
| `logits` / `logits_200` | unchanged | float | cuda/cpu | GZSL logits | no |

## Shape Invariants

- [x] Batch dimension is unchanged.
- [x] Class dimension is unchanged.
- [x] Train logits remain `[B (images), C_seen (seen classes)]`.
- [x] Eval logits remain `[B (images), C_all (all classes)]`.
- [x] Visual/text embedding dimensions remain scorer-compatible.
- [x] Seen/unseen class order is unchanged.
- [x] No unintended broadcasting is introduced.

## Config Switch

```text
switch: jepa_context_mode
values: embed | fae_memory | fae_main_memory
default: embed
trial config path: attempts/ATTEMPT-001/config.yaml
base config affected: no
```

```text
switch: jepa_text_mode
values: adapted | conditional
default: adapted
trial config path: attempts/ATTEMPT-001/config.yaml and attempts/ATTEMPT-002/config.yaml
base config affected: no
```

## Baseline-Off Path

`jepa_context_mode: embed` keeps the current AG-JEPA implementation: `context` and `target` are both computed from `cross_tf.embed_cv(patches)` before FAE. Existing configs that do not define `jepa_context_mode` default to `embed`.

`jepa_context_mode: fae_memory` is the TRIAL-001 keep-only variant: `_ag_jepa_loss` recomputes FAE on keep tokens only, then mean pools the keep-only memory as context. It is valid evidence for that leakage-avoidant variant, but it is not this TRIAL-002 strict main-path memory context.

`jepa_context_mode: fae_main_memory` is the TRIAL-002 strict main-path variant: `GTPJ.forward` passes the main `CrossModalTransformer.forward` `jepa_memory` into `compute_loss`, and `_ag_jepa_loss` mean-pools the kept positions from that main-path memory as context.

`jepa_text_mode: adapted` keeps the older AG-JEPA text condition: `all_text[labels] -> embed_text`.
`jepa_text_mode: conditional` is the TRIAL-002 text condition: `all_text_cond[batch, labels] -> embed_text`; the negative branch also uses `all_text_cond[batch, neg_labels]`.

## Loss Contract

```text
new loss name: no
lambda keys: lambda_jepa, lambda_jepa_neg
lambda=0 behavior: JEPA contributes nothing to total loss
normalization/reduction changes: none; existing mean reduction is preserved
```

## Evaluation Contract

```text
eval path changed: no
train logits shape: [B, 150] on CUB
eval logits shape: [B, 200] on CUB
class order: unchanged 0..199
metric calculation: unchanged GZSL U/S/H/ZS
```

## Checkpoint Contract

```text
new state_dict keys: none expected
old checkpoint load behavior: unchanged unless future code adds explicit parameters
missing/unexpected keys: none expected
```

## Risks

- TRIAL-002 intentionally tests strict main-path memory even though the kept memory may have interacted with masked tokens inside the main FAE self-attention.
- Selected patch alignment must be shared by mask, target, context, and geometry.
- Negative branch should detach visual context.
- `fae_memory` mode must reject `use_fae: false`.
- `jepa_text_mode: conditional` must reject configs without `use_conditional_text: true` and `conditional_text_ratio > 0`.

## Minimum Verification

- [x] Switch-off forward pass.
- [x] Switch-on forward pass.
- [x] Train/eval logits shape check.
- [x] Loss scalar and backward check.
- [x] FAE gradient probe.
- [x] Negative visual-context detach probe.
- [x] Full-patch mode check.
- [x] Main-path `jepa_memory` context probe for `fae_main_memory`.
- [x] Conditional AG-JEPA text probe with `meta_net` gradient.
- [x] Base config files unchanged.

## Verification Commands

```powershell
python -m py_compile model/MyModel.py train_GTPJ_CUB.py
python -m unittest tests.test_fae_memory_jepa
python -m unittest tests.test_gtpj_workflow
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
python workflow/gtpj_workflow.py validate-remote
git diff --check
```
