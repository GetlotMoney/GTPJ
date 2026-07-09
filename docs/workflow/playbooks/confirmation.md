# 执行卡：复现 / 确认 Confirmation

用于复现或确认一个结果。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/protocols/experiment_protocol.md
docs/workflow/protocols/quality_gate.md
产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
```

## 角色

正式默认角色：

```text
总控 (Coordinator)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

正式 confirmation / rerun 启动 Runner 前，必须写 `agent_runtime.yaml`，记录真实
左侧命名 Codex 线程，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。否则
confirmation 必须阻断；不能用单窗口 sequential review 生成 confirmed evidence。

## 复现 / Repeat 类型

必须先声明本轮是哪一种：

```text
exact_repeat:
  固定原始 code commit、config、original_seed、data/cache、epoch schedule、batch size 和评估口径。
  不允许换 seed，不允许换任何参数。
  max_attempts: 5
  max_attempts_hard_cap: true
  early_stop_on_best_hit: true
  restore_target_H: 原始结果水平，必须达到才算还原。
  near_miss_tolerance_H: 默认 0.2；只用于记录接近但未还原。
  near_miss_not_restored: 接近只能说明实验有效果、还有希望。
  用来回答“原始结果能不能原样再跑出来”。
  只有 exact_repeat 才能叫严格复现。

same_seed_repeat:
  同一个 original_seed 重跑，最多 5 次，命中即停。
  用来检查非确定性、环境漂移和同配置可重复性。

seed_sweep / score_search:
  主配置固定，但 seed 变化。
  用来冲分、找 seed 敏感性或观察稳定性；必须写 not_confirmation_evidence: true，不能叫严格复现，也不能单独作为 confirmed evidence。

multi_seed_stability:
  预先声明多个 seed，报告 mean/min/max/range。
  可作为稳定性证据，但必须和 exact_repeat 区分，并写 not_confirmation_evidence: true。
```

seed 是实验配置的一部分。改变 seed 就不是“同配置严格复现”，只能是
`seed_sweep`、`score_search` 或 `multi_seed_stability`。

默认 confirmation 必须写明 repeat 类型。正式复现默认 `repeat_type: exact_repeat`、
`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。一旦任一 clean run 达到 `restore_target_H`，
立刻停止后续 pending repeat；无论是否还原成功，同一候选最多 5 次，5 次未达到则收口为 not restored。落入 `near_miss_tolerance_H` 但未达到 `restore_target_H` 时，
只能写 `near_miss_not_restored`：说明实验有效果、还有希望，不能说还原，不能停止。

如果复现有单次命中：

```text
best_hit = true
best_single_H = best repeat H
best_observed_H = best repeat H
结论 = 命中候选 / 继续复现
```

如果稳定确认也通过：

```text
stable_confirm = true
confirmed_H = repeat mean 或协议指定的 confirmed metric
official single = best repeat
reported stability = mean / min / max
promotion_compare_metric = repeat mean / confirmed_H
```

不能隐藏较弱 repeat。稳定性属于正式证据的一部分。
不得只凭 best repeat 做 promotion 或 baseline claim。
不得把 multi-seed 的最高值写成 exact-repeat confirmed。
也不得用 mean H 掩盖单次最高命中；回答“有没有复现到”时优先报告 best single，
回答“能不能 promotion / baseline claim”时再报告 mean/min/max/range。

## 输出

版本级 confirmation：

```text
experiments/vX/confirmation/
```

trial 内部 confirmation：

```text
experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
attempts/ATTEMPT-xxx/
```
