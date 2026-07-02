# GTPJ-v4 Modules

```text
version: v4
parent_version: v3
status: legacy_config_only_not_framework_version
framework_diagram: framework_diagram.md
config: experiments/v4/config.yaml
```

## Module Table

| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|
| v3 framework code | Retain the v3 method state. | v3 inputs | v3 logits | inherited | unchanged from v3 |
| PSE / CLIP-A-self text adapter | Tune text residual strength. | class text features | `all_text [C,768]` | `pse_outer_ratio=0.5`, `clip_a_self_outer_ratio=0.5` | ratio 0 returns raw text blend; this tag only tunes the ratio |
| ICSA conditional text adaptation | Same as v3. | CLS token and text | `all_text_cond [B,C,768]` | `icsa_ratio=0.008` | unchanged from v3 |
| FGVD / FAE local memory | Same as v3. | selected patches | local visual memory | `use_fgvd_geometry` / `use_fae` | unchanged from v3 |
| BVSA local branch | Same as v3 with lower fusion weight. | local memory and text | `S_local [B,C]` | `local_weight=0.1` | `local_weight=0` removes local contribution |
| SGMP / AG-JEPA auxiliary training | Same as v3. | visual context and text | auxiliary losses | `lambda_mpp`, `lambda_neg`, legacy `lambda_jepa*` | lambda 0 removes auxiliary contribution |

## Config Switches

| Switch | Meaning |
|---|---|
| `pse_outer_ratio=0.5` | Historical tuned text residual ratio. |
| `local_weight=0.1` | Historical tuned local fusion ratio. |

## Version Delta

Compared with `v3`, this is pure parameter tuning. Under the current rule, pure tuning does not create a new formal framework version; `v4` is retained only as a legacy config-only record.
