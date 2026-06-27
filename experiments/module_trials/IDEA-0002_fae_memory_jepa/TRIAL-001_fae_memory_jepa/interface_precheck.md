# Interface Precheck: TRIAL-001_fae_memory_jepa

review_round: Review 1
role: Interface Checker
agent_instance_type: sub_agent
decision: revise
runner_status: blocked_until_review_2_and_gradient_probe_pass

## Inputs Checked

- `docs/workflow/code_interface_contract.md`
- `docs/workflow/innovation_code_review_protocol.md`
- `model/MyModel.py`
- `config/GTPJ_cub_gzsl.yaml`
- `train_GTPJ_CUB.py`
- `idea_tree/idea_tree.json`
- trial README / implementation.md / config.yaml

## Findings

- The concept is interface-compatible if implemented as a JEPA-only auxiliary-loss mode.
- Current active config lacks an explicit baseline-off switch. Add trial-local `jepa_context_mode: embed | fae_memory`; default/off path must be `embed`, preserving current AG-JEPA behavior.
- Existing AG-JEPA bypasses FAE. New `fae_memory` mode must expose or recompute an FAE-backed context without changing logits, class order, label mapping, eval, or metric semantics.
- LastViT alignment is the key risk: mask, `patch_z`, and FAE context must be computed on the same selected patch set.

## Insertion Point

- `model/MyModel.py::CrossModalTransformer.forward`: return selected CLIP patches, `patch_z = embed_cv(selected_patches)`, FAE `memory`, and selected indices as auxiliary outputs.
- `model/MyModel.py::GTPJ.forward`: pass auxiliary tensors in `out_package`; do not alter `base_logits`, `local_score`, `logits_200`, or `clip_S_pp`.
- `model/MyModel.py::GTPJ._ag_jepa_loss`: switch by `jepa_context_mode`.

## Input / Output Contract

- `patches`: `[B（图片/样本数量）, N（视觉 patch 数）, 768（CLIP 视觉维度）]`, float, cuda.
- selected patches in `fae_memory` mode: `[B, K_sel, 768]`, where `K_sel = lastvit_select_k` when active.
- `patch_z`: `[B, K_sel, 512]`, FAE-pre visual target source.
- FAE context source: `[B, K_keep, 512]`, computed from keep tokens of the same selected patch set.
- `all_text[labels]`: `[B, 768]`, seen class text already goes through CLIP-A-self adapter, then `cross_tf.embed_text`.
- `target`: `mean(masked patch_z).detach() -> [B, 512]`.
- `context`: `mean(keep-only FAE memory) -> [B, 512]`.
- `pred`: `[B, 512]`; JEPA losses remain scalar.

## Shape / Split Invariants

- Train logits remain `[B（图片/样本数量）, C_seen（seen 类数量，CUB=150）]`.
- Eval logits remain `[B（图片/样本数量）, C（全部类别数，CUB=200）]`.
- `logits_200` global class order remains 0..199.
- Training labels remain global ids and are mapped by `_global_to_seen_labels`.
- No unseen labels enter CE or JEPA positive labels.
- GZSL U/S/H/ZS calculation and unseen bias path stay unchanged.

## Baseline-Off Path

- `jepa_context_mode: embed` must preserve current AG-JEPA: context and target both from pre-FAE `patch_z`.
- `lambda_jepa=0` and `lambda_jepa_neg=0` must remove JEPA contribution from total loss.
- `jepa_context_mode: fae_memory` requires `use_fae: true`; otherwise raise `ValueError`.

## Minimum Verification Plan

- Switch-off equivalence: `jepa_context_mode=embed` gives unchanged logits shape, loss keys, and class order.
- Switch-on smoke: small random/cached batch forward with `is_train=True` returns `[B,150]`; eval returns `[B,200]`.
- Backward smoke: total loss finite and `.backward()` succeeds.
- Gradient probe: positive JEPA loss gives nonzero grad on `cross_tf.fae.*`, `cross_tf.embed_cv`, `cross_tf.embed_text`, `jepa_predictor`, and CLIP-A-self adapter parameters.
- Negative probe: with negative loss only, detached visual context should not create FAE gradient.
- Eval probe: `eval_zs_gzsl` still consumes `[B,200]` logits and reports U/S/H/ZS with unchanged semantics.

## Decision

revise. Implementer must add the explicit mode switch and preserve the contracts above. Runner remains blocked until Review 2 verifies the diff and gradient evidence.

## Evidence Refs

- `model/MyModel.py`
- `config/GTPJ_cub_gzsl.yaml`
- `train_GTPJ_CUB.py`

memory_used: yes
memory_sources: docs/workflow/agents/shared_roles/interface_checker/memory.md
verified_against_current_repo: yes
