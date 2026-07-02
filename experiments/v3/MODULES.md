# GTPJ-v3 Modules

```text
version: v3
parent_version: v2
framework_diagram: framework_diagram.md
config: experiments/v3/config.yaml
```

## Module Table

| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|
| Frozen CLIP ViT-L/14@336px | Fixed visual feature extractor. | image batch | `clip_features [B,577,768]` | external backbone setup | not switchable in GTPJ config |
| PSE / CLIP-A-self text adapter | Adapt seen-class text prototypes. | GPT text features | `all_text [C,768]` | `use_clip_a_self`, `clip_a_self_*` | disabled returns raw text prototypes |
| ICSA conditional text adaptation | Inject per-image visual context into class prototypes. | CLS token and `all_text` | `all_text_cond [B,C,768]` | `use_conditional_text`, `conditional_text_ratio`, `meta_net_hidden` | disabled or ratio 0 returns shared text |
| LastViT / FGVD patch selection | Select informative local visual tokens. | patch tokens | selected patches | `lastvit_select_k`, `lastvit_select_formula` | falls back to baseline patch selection |
| FAE geometry-aware visual memory | Build local memory for the main path. | selected patches | `jepa_memory` / local memory | `use_fae` | disabled returns non-FAE local context |
| BVSA bidirectional local branch | Produce local class score. | local visual memory and text | `S_local [B,C]` | transformer and fusion config | `local_weight=0` removes local contribution |
| AG-JEPA auxiliary training | Use main-path FAE memory and conditional text to regularize local semantics. | `jepa_memory`, patch targets, text | auxiliary losses | `jepa_context_mode=fae_main_memory`, `jepa_text_mode=conditional`, `lambda_jepa`, `lambda_jepa_neg` | lambda 0 removes auxiliary contribution |

## Config Switches

| Switch | Meaning |
|---|---|
| `jepa_context_mode=fae_main_memory` | AG-JEPA reads the same kept positions as the main FAE path. |
| `jepa_text_mode=conditional` | AG-JEPA text predictor uses sample-conditioned text. |
| `conditional_text_ratio=0.008` | Strength of ICSA text injection. |
| `local_weight=0.3` | Local branch contribution to final logits. |

## Version Delta

Compared with `v2`, `v3` adds the owner-corrected strict FAE-memory JEPA path and conditional AG-JEPA text input. It is a formal code snapshot with unconfirmed stochastic evidence.
