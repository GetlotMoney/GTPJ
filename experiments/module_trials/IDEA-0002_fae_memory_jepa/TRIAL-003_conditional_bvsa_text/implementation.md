# Implementation Record

## Module

Conditional BVSA text input with framework-name code aliases.

## Motivation

Make ICSA (`image_conditioned_semantic_adapter(cls_token)`) directly condition BVSA, so `decoder_v2s` and `decoder_s2v` consume the same sample-conditioned text used by `S_global` and SGMP.

## Attachment Point

| Item | Value |
|---|---|
| File | `model/MyModel.py` |
| Class/function | `GTPJ.forward`; `BidirectionalVisualSemanticAlignment.forward` |
| Before/after | Before: BVSA receives `all_text [C,768]`. After: optional `all_text_cond [B,C,768]`. |
| Consumes | `all_text`, `all_text_cond`, `patches`, `cls_token` |
| Produces | `S_local / local_score [B,C]`, `score_v2s [B,C]`, `score_s2v [B,C]` |

## Input Contract

| Name | Shape | Dtype | Device | Meaning | Gradients |
|---|---|---|---|---|---|
| `all_text` | `[C class count, 768 CLIP dimension]` | float | model device | Shared class prototypes after CLIP-A-self | yes |
| `all_text_cond` | `[B image count, C class count, 768 CLIP dimension]` | float | model device | Per-image class prototypes from ICSA (`image_conditioned_semantic_adapter(cls_token)`) | yes |
| `patches` | `[B image count, P patch count, 768 CLIP dimension]` | float | model device | CLIP visual patch tokens | yes |

## Output Contract

| Name | Shape | Dtype | Device | Meaning | Replaces existing variable? |
|---|---|---|---|---|---|
| `S_local` / `local_score` | `[B image count, C class count]` | float | model device | BVSA local class score | no, same output shape |
| `score_v2s` | `[B image count, C class count]` | float | model device | Visual-to-semantic branch score | no |
| `score_s2v` | `[B image count, C class count]` | float | model device | Semantic-to-visual branch score | no |

## Shape Invariants

- [x] Batch dimension is unchanged.
- [x] Class dimension is unchanged.
- [x] Logits shape remains `[B image count, C class count]`.
- [x] Visual/text embedding dimensions remain compatible with the base scorer.
- [x] Seen/unseen class order is unchanged.
- [x] Label mapping is unchanged.
- [x] Batched BVSA text checks batch size explicitly before decoding.

## Config Switch

```text
switch: bvsa_text_mode
default: adapted
trial config path: experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text/attempts/ATTEMPT-001/config.yaml
base config affected: config/versions/v3.yaml, experiments/v3/config.yaml, and experiments/v3/baseline/config.yaml now include framework-name aliases and explicit bvsa_text_mode=conditional
```

## Baseline-Off Path

`bvsa_text_mode=adapted` keeps old v3 behavior: BVSA receives `all_text [C,768]`, expands it to `[B,C,512]`, and computes the same score shapes as before.

## Framework Name Aliases

| Framework name | Code name | Legacy alias kept |
|---|---|---|
| Progressive Semantic Enhancement (PSE) | `pse_adapter_ratio`, `use_pse_self_attention`, `pse_*`, `SemanticPrototypeAdapter`, `ProgressiveSemanticSelfAttention` | `adapter_ratio`, `use_clip_a_self`, `clip_a_self_*`, `Adapter`, `CLIPASelfAdapter` |
| Image-Conditioned Semantic Adapter (ICSA) | `use_icsa`, `icsa_ratio`, `image_conditioned_semantic_adapter`, `icsa_hidden` | `use_conditional_text`, `conditional_text_ratio`, `meta_net`, `meta_net_hidden` |
| Frequency-Guided Visual Disentanglement (FGVD) | `fgvd_select_*`, `use_fgvd_geometry`, `fgvd_memory` | `lastvit_select_*`, `use_fae`, `jepa_memory` |
| Semantic-Guided Masked Prediction (SGMP) | `use_sgmp`, `sgmp_context_mode`, `sgmp_text_mode`, `loss_mpp`, `loss_neg` | `use_ag_jepa`, `jepa_context_mode`, `jepa_text_mode`, `loss_jepa`, `loss_jepa_neg` |
| Bidirectional Visual-Semantic Alignment (BVSA) | `bvsa_text_mode`, `BidirectionalVisualSemanticAlignment`, `bvsa` | `CrossModalTransformer`, `cross_tf` |

## Loss Contract

```text
new loss: none
lambda key: none
lambda=0 behavior: not applicable
normalization/reduction changes: none
```

## Evaluation Contract

```text
eval path changed: S_local / local_score text input can be conditional when CLS token exists
logits shape: unchanged
class order: unchanged
label mapping: unchanged
seen/unseen split: unchanged
metric calculation: unchanged
metric semantics: unchanged
```

## Checkpoint Contract

```text
new state_dict keys: none
old checkpoint load behavior: unchanged
missing/unexpected keys: none expected from this change
```

## Risk

- Conditional BVSA text increases coupling between ICSA and both BVSA branches.
- Patch-only inputs cannot build `all_text_cond`; conditional mode raises instead of silently falling back.

## Minimum Verification

- [x] Default/adapted BVSA local score does not reach ICSA.
- [x] Conditional BVSA local score reaches ICSA.
- [x] `S_local / local_score`, `score_v2s`, and `score_s2v` remain `[B,C]`.
- [x] Framework-only config keys drive the model.
- [x] Legacy-only config keys still work.
- [x] Framework keys take priority when old and new aliases conflict.
- [x] Python compile passes.
- [ ] Full training not run.

## Verification Command

```bash
python -m unittest tests.test_fae_memory_jepa
python -m unittest tests.test_fae_memory_jepa tests.test_gtpj_workflow
python -m py_compile model/MyModel.py train_GTPJ_CUB.py
```
