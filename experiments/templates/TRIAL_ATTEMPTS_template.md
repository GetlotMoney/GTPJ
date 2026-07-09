# TRIAL ATTEMPTS（试验尝试记录）

本文件记录一个 `TRIAL-xxx` 内部的多次参数尝试、窄范围后续消融、confirmation、rerun 或 debug-fix rerun。
它不是正式 baseline 的 `tune/INDEX.md`，也不替代 trial root 决策文件。
它是本 trial 内部 formal_pending 的 owner-facing 正式表格；owner 问“有哪些待跑实验”时，本表必须能直接回答。

## Attempts（尝试列表）

| Attempt ID | Type | Run ID | Formal | Status | Evidence state | 参数 / 变化 | 旧值 | 新值 | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | param_tune | `RUN-...` | true | planned | pre_run | `clip_a_self_outer_ratio` | 0.20 | 0.10 | 5 | pending | pending | pending | pending | pending | pending | pending | `attempts/ATTEMPT-001/` |

## Type Rules（类型规则）

```text
param_tune       # 只改变数值或既有 config 值
ablation         # 同一 trial 内的局部诊断消融
rerun            # 用于 confirmation 或失败恢复的 same config / original_seed exact repeat
anchor_followup  # 围绕 drift/anchoring risk 的窄范围 follow-up
debug_fix        # 只在修复环境或 runner 问题后 rerun
```

## Notes（备注）

- `ATTEMPT-xxx` 必须 append-only，不要覆盖旧 attempts。
- 每个 attempt 应有自己的 `config.yaml`、`manifest.yaml`、`result.yaml`、`quality_check.md` 和 `result.md`。
- trial root 的 `README.md` 应指向当前驱动决策的 `best_attempt_id`。
- 如果改动不再是窄范围 attempt，而是变成新的实现假设，打开 `TRIAL-002`，不要继续扩展本表。
- 待跑正式实验必须在本表显示为 `planned`、`pending`、`pre_run`、`pre_run_gated` 或 `ready_to_run`。
- `.gtpj_runtime` 目录不是正式待跑表；没有本表对应行的运行目录统一视为 `orphan_runtime_plan`。
- `debug_smoke` 必须写 `Formal=false`，不能混入正式待跑或 keep / best / confirmation / promotion。
- 正式复现必须写 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、
  `max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、
  `near_miss_not_restored`；只有达到 `restore_target_H` 后才停止后续 pending repeat。
- 同一候选不管是否还原成功，最多 5 次 exact repeat；5 次未达目标时收口为 not restored / near miss，不能继续加跑复现。
- 接近但未达到目标只能写 `near_miss_not_restored`：有效果、还有希望，不能说还原。
- `seed_sweep`、`score_search` 或 `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，
  不能冒充复现。
