# GTPJ-v5 Modules

```text
version: v5
parent_version: v3
framework_diagram: framework_diagram.md
config: experiments/v5/config.yaml
trial_framework_source: experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text/framework_diagram.md
```

## Module Table

| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|
| Frozen CLIP ViT-L/14@336px | Fixed visual feature extractor. | image batch | `clip_features [B,577,768]` | external backbone setup | not switchable in GTPJ config |
| PSE / CLIP-A-self text adapter | Adapt seen-class GPT text prototypes before image conditioning. | class text features | `all_text [C,768]` | `use_pse_self_attention`, `pse_inner_ratio`, `pse_outer_ratio`; legacy `use_clip_a_self`, `clip_a_self_*` | disabling self-attention or using zero residual returns the raw/shared text path |
| ICSA conditional text adaptation | Inject image-conditioned semantic residuals into class prototypes. | CLS token and `all_text` | `all_text_cond [B,C,768]` | `use_icsa`, `icsa_ratio`, `icsa_hidden`; legacy `use_conditional_text`, `conditional_text_ratio`, `meta_net_hidden` | disabled or ratio 0 returns `all_text` |
| FGVD patch selection | Select local patches for the visual memory branch. | CLIP patch tokens | selected patches `[B,K,768]` | `fgvd_select_k=32`, `fgvd_select_formula=v2_abs_mean`; legacy `lastvit_select_*` | falls back to the parent local patch-selection behavior |
| FGVD geometry-aware visual memory | Encode selected patches into local memory. | selected patches | local memory `[B,K,512]` | `use_fgvd_geometry`; legacy `use_fae` | disabled returns non-geometry local memory path |
| BVSA bidirectional visual-semantic alignment | Produce local class scores through V2S and S2V decoders. | FGVD memory and text input | `S_local [B,C]` plus branch scores | `bvsa_text_mode=conditional`, `weight_s2v`, transformer config | `bvsa_text_mode=adapted` sends shared `all_text [C,768]` into BVSA, matching the older path |
| Local/global fusion | Combine global and local scores. | `S_global [B,C]`, `S_local [B,C]` | `S_final [B,C]` | `local_weight=0.2` | `local_weight=0` removes local branch contribution |
| Consistency / BMDD legacy loss | Keep global/local score behavior aligned. | global and local scores | scalar auxiliary loss | `lambda_consist`, `lambda_bmdd`; legacy `lambda_msdn` | lambda 0 removes the auxiliary loss |
| SGMP / AG-JEPA auxiliary training | Use FGVD memory and conditional text for semantic masked prediction and negative suppression. | FGVD memory, patch targets, conditional text | `L_mpp`, `L_neg` | `use_sgmp`, `sgmp_context_mode=fgvd_main_memory`, `sgmp_text_mode=conditional`, `lambda_mpp`, `lambda_neg`; legacy `use_ag_jepa`, `jepa_*` | disabled or lambda 0 removes auxiliary contribution |

## Config Switches

| Switch | Meaning |
|---|---|
| `bvsa_text_mode=conditional` | Main v5 route: BVSA consumes `all_text_cond [B,C,768]`. |
| `pse_outer_ratio=0.65` | Stronger text prototype residual than the v3/v4 confirmed config. |
| `icsa_ratio=0.008` | Conditional semantic injection strength. |
| `local_weight=0.2` | BVSA local score weight in final logits. |
| `sgmp_text_mode=conditional` | SGMP reads conditional text rather than shared class text. |

## Version Delta

Compared with `v3`, `v5` activates the TRIAL-003 conditional BVSA text path and freezes the `trial003-main100-069` source config. It is owner-activated for future tuning. Its repeat mean does not beat the stronger confirmed `v3/CONFIRM-001 local-v3-054` reference, so v5 must not be described as a stronger confirmed baseline.
