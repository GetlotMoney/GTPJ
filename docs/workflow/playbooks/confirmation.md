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
右侧临时 agents，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。否则
confirmation 必须阻断；不能用单窗口 sequential review 生成 confirmed evidence。

## 复现 / Repeat 类型

必须先声明本轮是哪一种：

```text
exact_repeat:
  固定原始 code commit、config、seed、data/cache、epoch schedule、batch size 和评估口径。
  用来回答“原始结果能不能原样再跑出来”。
  只有 exact_repeat 才能叫严格复现。

same_seed_min3:
  同一个原始 seed 重跑 3 次。
  用来检查非确定性、环境漂移和同配置可重复性。

seed_sweep / score_search:
  主配置固定，但 seed 变化。
  用来冲分、找 seed 敏感性或观察稳定性；不能叫严格复现，也不能单独作为 confirmed evidence。

multi_seed_stability:
  预先声明多个 seed，报告 mean/min/max/range。
  可作为稳定性证据，但必须和 exact_repeat 区分。
```

seed 是实验配置的一部分。改变 seed 就不是“同配置严格复现”，只能是
`seed_sweep`、`score_search` 或 `multi_seed_stability`。

默认 confirmation 跑 3 次，但必须写明 repeat 类型。

如果复现通过：

```text
official single = best repeat
reported stability = mean / min / max
promotion_compare_metric = repeat mean / confirmed_H
```

不能隐藏较弱 repeat。稳定性属于正式证据的一部分。
不得只凭 best repeat 做 promotion 或 baseline claim。
不得把 multi-seed 的最高值写成 exact-repeat confirmed。

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
