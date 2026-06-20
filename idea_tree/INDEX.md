# Idea Tree Index

Current framework version: `v1`

This is the human-readable master list. For the current work window,
sort by `v1` score first. `global_score` is long-term value,
not the immediate experiment order.

| Rank | Idea | Title | Idea file | Source status | Global | Current score | Applicability | Status | Next action |
|---:|---|---|---|---|---:|---:|---|---|---|
| 1 | `IDEA-0001` | LaSt-ViT CLS replacement | `idea_tree/ideas/IDEA-0001_lastvit_cls/IDEA.md` | unverified | 55 | 55 | needs_adaptation | candidate | Verify the cited paper/source, then decide whether to create a small module trial. |
| 2 | `IDEA-0008` | Attribute-patch OT alignment | `idea_tree/ideas/IDEA-0008_attr_patch_ot/IDEA.md` | unverified | 50 | 50 | direct | candidate | Verify OT/patch-attribute grounding source before trial. |
| 3 | `IDEA-0006` | Geometry-aware attribute routing | `idea_tree/ideas/IDEA-0006_geo_attribute_routing/IDEA.md` | unknown | 50 | 50 | direct | candidate | Find paper/source support for attribute routing or mark as local idea before trial. |
| 4 | `IDEA-0009` | Uncertainty-aware MSDN gate | `idea_tree/ideas/IDEA-0009_uncertainty_msdn_gate/IDEA.md` | unknown | 50 | 50 | direct | candidate | Document whether this is local confidence gating or paper-backed before trial. |
| 5 | `IDEA-0002` | Dynamic local branch gating and pooling | `idea_tree/ideas/IDEA-0002_dynamic_local_gating/IDEA.md` | unknown | 45 | 45 | needs_adaptation | candidate | Split into one-variable trials only after source or rationale is documented. |
| 6 | `IDEA-0007` | Topology-aware text attribute reservoir | `idea_tree/ideas/IDEA-0007_text_attribute_reservoir/IDEA.md` | unknown | 45 | 45 | needs_adaptation | candidate | Clarify source and decide if this should be tested before attribute routing. |
| 7 | `IDEA-0004` | AG-JEPA neighbor-text variant | `idea_tree/ideas/IDEA-0004_ag_jepa_neighbor_text/IDEA.md` | unknown | 40 | 40 | direct | candidate | Document whether this is a local variant or paper-backed before trial. |
| 8 | `IDEA-0005` | Counterfactual negative text margin | `idea_tree/ideas/IDEA-0005_counterfactual_negative_text/IDEA.md` | unknown | 40 | 40 | direct | candidate | Record a reference source or mark as local heuristic before trial. |
| 9 | `IDEA-0003` | Cosine-only CrossModal scoring with anchor losses | `idea_tree/ideas/IDEA-0003_cosine_only_scoring/IDEA.md` | unknown | 35 | 35 | needs_adaptation | candidate | Require source/rationale review before any trial because this changes the main scoring path. |
| 10 | `IDEA-0010` | Seen-unseen calibration losses | `idea_tree/ideas/IDEA-0010_seen_unseen_calibration/IDEA.md` | unknown | 30 | 30 | needs_adaptation | candidate | Find a GZSL calibration reference before selecting this as a trial. |

## Version-Aware Rule

- Use the active version score column for experiment order.
- Add a new `version_scores.vX` entry when a new framework version exists.
- Do not copy an old version score into a new version without reviewing interface fit.
- A high `global_score` with a low current score means the idea may be useful later, not now.
