# TRIAL ATTEMPTS

本文件记录一个 `TRIAL-xxx` 内部的多次参数尝试、窄范围后续消融、rerun 或 debug-fix rerun。
它不是正式 baseline 的 `tune/INDEX.md`，也不替代 trial root 决策文件。

## Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | param_tune | `clip_a_self_outer_ratio` | 0.20 | 0.10 | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | `log:...` | keep | `attempts/ATTEMPT-001/` |

## Type Rules

```text
param_tune       # 只改变数值或既有 config 值
ablation         # 同一 trial 内的局部诊断消融
rerun            # 用于 confirmation 或失败恢复的同 config rerun
anchor_followup  # 围绕 drift/anchoring risk 的窄范围 follow-up
debug_fix        # 只在修复环境或 runner 问题后 rerun
```

## Notes

- `ATTEMPT-xxx` 必须 append-only，不要覆盖旧 attempts。
- 每个 attempt 应有自己的 `config.yaml`、`manifest.yaml`、`result.yaml`、`quality_check.md` 和 `result.md`。
- trial root 的 `README.md` 应指向当前驱动决策的 `best_attempt_id`。
- 如果改动不再是窄范围 attempt，而是变成新的实现假设，打开 `TRIAL-002`，不要继续扩展本表。
