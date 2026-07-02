# GTPJ-v2 Modules

```text
version: v2
parent_version: v1
framework_diagram: framework_diagram.md
config: experiments/v2/config.yaml
```

## Module Table

| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|
| Frozen CLIP ViT-L/14@336px | Fixed visual feature extractor. | image batch | `clip_features [B,577,768]` | external backbone setup | not switchable in GTPJ config |
| GPT/VDT sentence text prototypes | Preserve sentence-level text evidence before pooling. | GPT/VDT descriptions | sentence text features | `text_source` | uses selected text source |
| CLIP-A-self text prototype adapter | Let seen-class sentence prototypes interact before class pooling. | sentence-level text features | adapted seen class text | `use_clip_a_self`, `clip_a_self_heads`, `clip_a_self_dropout` | disabled returns the v1 text path |
| Inner/outer text residual blend | Control how much CLIP-A-self changes text prototypes. | raw and adapted text | `all_text [C,768]` | `clip_a_self_inner_ratio`, `clip_a_self_outer_ratio` | ratios 0 return raw text |
| Conditional text adapter | Adds image-conditioned text residual. | CLS token and `all_text` | `all_text_cond [B,C,768]` | `use_conditional_text`, `conditional_text_ratio` | disabled or ratio 0 returns shared class text |
| Local visual-text branch | Computes local score from selected patches. | selected patches and text | `S_local [B,C]` | `local_weight`, transformer config | `local_weight=0` removes local contribution |
| AG-JEPA auxiliary training | Keeps auxiliary semantic prediction pressure. | visual context and text | auxiliary losses | `use_ag_jepa`, `lambda_jepa`, `lambda_jepa_neg` | lambda 0 removes the auxiliary loss |

## Config Switches

| Switch | Meaning |
|---|---|
| `clip_a_self_apply_unseen=false` | Do not adapt unseen-class prototypes directly. |
| `clip_a_self_inner_ratio=0.35` | Sentence-level residual blend inside seen-class text adaptation. |
| `clip_a_self_outer_ratio=0.15` | Final residual blend against raw class text prototypes. |
| `local_weight=0.3` | Local branch contribution to final logits. |

## Version Delta

Compared with `v1`, `v2` adds the CLIP-A-self text prototype adapter and records `ATTEMPT-019` as best observed evidence. It is owner-activated but not clean-confirmed.
