# Review 1: Interface Precheck

```text
decision: allow
activation_mode: role_only_code_preparation
```

## Design

Add `bvsa_text_mode`:

```text
adapted     -> BVSA receives all_text [C,768]
conditional -> BVSA receives all_text_cond [B,C,768]
```

Code now uses the framework name `BidirectionalVisualSemanticAlignment`; `CrossModalTransformer` remains only as a compatibility alias.

## Interface Checks

- Batch dimension remains `B`.
- Class dimension remains `C=200`.
- `S_final / logits_200`, `S_local / local_score`, `score_v2s`, and `score_s2v` remain `[B,C]`.
- Class order, label mapping, seen/unseen split, and metric calculation are unchanged.
- Conditional BVSA mode requires `use_icsa=True` and a positive `icsa_ratio`; `use_conditional_text` and `conditional_text_ratio` remain legacy aliases.
- Framework-name config aliases (`fgvd_*`, `use_sgmp`, `sgmp_*`, `lambda_mpp`, `lambda_neg`, `lambda_bmdd`) must remain compatible with legacy aliases.
- Patch-only input without `cls_token` must raise instead of silently falling back.

## Writable Files

- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `config/GTPJ_cub_gzsl.yaml`
- `tests/test_fae_memory_jepa.py`
- trial-local lightweight records
