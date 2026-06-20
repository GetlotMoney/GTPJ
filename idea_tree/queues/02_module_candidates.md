# Module Candidates

These are module candidates migrated from inactive or alternative paths in the
current v1 code. They are not selected for implementation yet, and their
switches are not part of the v1 baseline config.

This queue is a working view derived from `idea_tree/INDEX.md`. Do not use this
file as the source of truth for ranking; update `idea_tree/INDEX.md`,
`idea_tree/idea_tree.json`, and the relevant `ideas/IDEA-xxxx_slug/IDEA.md`
file instead.

Rule: before any trial starts, the source must be verified or the idea must
remain explicitly marked as `source_status: unknown` / `unverified`.
When a candidate is selected, add its switch only to the trial-local
`config.yaml`.

| Idea | Candidate | Main switches | Source status | Priority | Next action |
|---|---|---|---|---:|---|
| `IDEA-0001` | LaSt-ViT CLS replacement | `use_lastvit_cls` | unverified | 0.55 | Verify cited paper/source before trial. |
| `IDEA-0002` | Dynamic local branch gating and pooling | `gating_dynamic`, `weight_s2v_mode`, `pool_method=dmp`, `pool_dynamic` | unknown | 0.45 | Split into one-variable trials only after rationale/source is recorded. |
| `IDEA-0003` | Cosine-only CrossModal scoring with anchor losses | `score_mode=cosine_only`, anchor/distill/aux losses | unknown | 0.35 | Require source/rationale review before touching scoring path. |
| `IDEA-0004` | AG-JEPA neighbor-text variant | `use_ag_jepa_v2` | unknown | 0.40 | Decide whether this is local or paper-backed. |
| `IDEA-0005` | Counterfactual negative text margin | `use_cf_neg_text` | unknown | 0.40 | Record source or local-heuristic rationale before trial. |
| `IDEA-0006` | Geometry-aware attribute routing | `use_geo_attr_routing` | unknown | 0.50 | Find source support or mark as local idea before trial. |
| `IDEA-0007` | Topology-aware text attribute reservoir | `use_text_attr_reservoir` | unknown | 0.45 | Clarify source and relation to topology loss. |
| `IDEA-0008` | Attribute-patch OT alignment | `use_attr_patch_ot` | unverified | 0.50 | Verify OT/patch-attribute grounding source. |
| `IDEA-0009` | Uncertainty-aware MSDN gate | `use_uncertainty_msdn_gate` | unknown | 0.50 | Document confidence-gating source or local rationale. |
| `IDEA-0010` | Seen-unseen calibration losses | `lambda_cal`, `lambda_bias` | unknown | 0.30 | Find GZSL calibration reference before selecting. |

Not module candidates:

- `use_unzip`, `use_gpt`, `lambda_reg`, `lambda_con`: old inert config keys with no code references.
- `use_aug_cache`: runtime/cache control, not a model module.
- `use_amp`: runtime optimization, not a model module.
- `model_mode=clip_only/adapter_only`: ablation controls, not new modules.
