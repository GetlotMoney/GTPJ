# Review 2: Code Diff Pre-Run

```text
decision: allow_for_smoke_and_pre_run_freeze
activation_mode: role_only_code_preparation
formal_runner_status: not_started
```

## Checked

- `BidirectionalVisualSemanticAlignment.forward` accepts `[C,D]` and `[B,C,D]` text.
- Batched text checks batch size before decoder calls.
- `score_s2v` uses per-sample class text in conditional mode.
- `GTPJ.forward` uses `all_text_cond` only when `bvsa_text_mode=conditional`.
- `bvsa_text_mode` defaults to `adapted`, preserving baseline-off behavior.
- Tests prove conditional BVSA text reaches ICSA through `S_local / local_score`.
- Tests prove framework-only config keys work, legacy-only config keys still work, and framework keys override legacy aliases on conflicts.
- Quality Checker initially blocked incomplete naming/test coverage; this was resolved by adding PSE/ICSA config aliases, marking old keys as legacy aliases, and adding config compatibility tests.

## Blocking Issues

None for local shape/backward and config-alias verification.

Formal training still requires a pre-run freeze commit and clean worktree.
