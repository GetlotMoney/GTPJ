# Review 1: Interface Precheck

```text
decision: allow
activation_mode: role_only_code_preparation
```

## Design

Add `bvsa_text_mode`:

```text
adapted     -> CrossModalTransformer receives all_text [C,768]
conditional -> CrossModalTransformer receives all_text_cond [B,C,768]
```

## Interface Checks

- Batch dimension remains `B`.
- Class dimension remains `C=200`.
- `logits_200`, `local_score`, `score_v2s`, and `score_s2v` remain `[B,C]`.
- Class order, label mapping, seen/unseen split, and metric calculation are unchanged.
- Conditional BVSA mode requires `use_conditional_text=True` and a positive `conditional_text_ratio`.
- Patch-only input without `cls_token` must raise instead of silently falling back.

## Writable Files

- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `config/GTPJ_cub_gzsl.yaml`
- `tests/test_fae_memory_jepa.py`
- trial-local lightweight records
