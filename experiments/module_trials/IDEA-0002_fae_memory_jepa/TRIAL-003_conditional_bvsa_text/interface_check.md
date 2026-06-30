# Interface Check

```text
decision: pass_for_code_verification
```

## Evidence

```bash
python -m unittest tests.test_fae_memory_jepa
python -m unittest tests.test_fae_memory_jepa tests.test_gtpj_workflow
python -m py_compile model/MyModel.py train_GTPJ_CUB.py
```

## Result

- `S_local / local_score`: `[B image count, C class count]`
- `score_v2s`: `[B image count, C class count]`
- `score_s2v`: `[B image count, C class count]`
- `all_text_cond`: `[B image count, C class count, 768 CLIP dimension]`
- Framework-only, legacy-only, and conflict-priority config paths are covered by unit tests.

No class-order, seen/unseen split, label mapping, logits shape, or metric calculation change is introduced by this code patch.
