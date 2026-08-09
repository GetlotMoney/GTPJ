# GTPJ-v1 Modules

```text
version: v1
framework_diagram: framework_diagram.md
config: experiments/v1/config.yaml
evidence_scope: version-level module glossary
```

## Module Table

| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|
| Frozen CLIP ViT-L/14@336px | Provide fixed visual features. | image batch | `clip_features [B,577,768]` | external backbone setup | not a switchable GTPJ module |
| GPT text prototypes | Provide class semantic anchors. | class descriptions | `all_text [C,768]` | `text_source` | falls back to the selected text source only |
| Text adapter | Residually adapts class text prototypes. | `all_text [C,768]` | adapted text prototypes | `adapter_ratio` | ratio 0 returns the raw text path |
| Patch selection | Selects local visual tokens. | CLIP patch tokens | selected patches `[B,K,768]` | `lastvit_select_k`, `lastvit_select_formula` | disabling selection would use the baseline patch path |
| Geometry-aware local visual encoder | Builds local visual memory. | selected patches | local memory | `use_fae` | off path should reduce to the non-geometry local branch |
| Bidirectional visual-text branch | Computes local class scores. | local visual memory and text prototypes | `S_local [B,C]` | transformer/local-branch config | `local_weight=0` removes its contribution from final logits |
| Conditional text adapter | Adds image-conditioned text residuals. | CLS token and class text | `all_text_cond [B,C,768]` | `use_conditional_text`, `conditional_text_ratio` | disabled or ratio 0 returns shared text prototypes |
| AG-JEPA auxiliary training | Adds semantic-guided auxiliary supervision. | visual context and text prototypes | auxiliary losses | `use_ag_jepa`, `lambda_jepa`, `lambda_jepa_neg` | lambda 0 removes the auxiliary loss |

## Config Switches

| Switch | Meaning |
|---|---|
| `local_weight` | Weight of local branch score in final fusion. |
| `lambda_consist` | Weight of local/global consistency loss. |
| `lambda_topo_pearson` | Weight of topology-preserving text constraint. |
| `lambda_msdn` | Weight of local/global distillation-style loss. |
| `lambda_jepa`, `lambda_jepa_neg` | Weights of AG-JEPA positive and negative auxiliary losses. |

## Version Delta

`v1` is the initial formal baseline, so the delta is relative to no earlier GTPJ version.
