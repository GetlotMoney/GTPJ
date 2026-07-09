# 执行卡：调参 Tune

用于参数、seed、epoch、batch、loss weight 或不改变方法语义的窄配置搜索。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
docs/workflow/protocols/experiment_protocol.md
产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
```

如果调参发生在 module trial 内部，还要读：

```text
docs/workflow/protocols/module_trial_protocol.md
```

## 角色

正式 tune 默认使用 `real_multi_agent`：

```text
总控 (Coordinator)
调参规划 (Tune Planner)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

正式 Runner 启动前必须写 `agent_runtime.yaml`，记录左侧命名 Codex 线程的真实
`agent_instance_id`，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。
否则正式 tune 必须阻断。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，
才允许继续；该结果不能进入 keep / best / confirmation / promotion。

## 输出

版本级 tune：

```text
experiments/vX/tune/
```

trial 内部 tune：

```text
experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/
```

raw logs 和 checkpoints 留在 Warehouse。

## 决策规则

只调参数带来的提升不能开新的 `vX`。

重要 tuned config 必须经过 `repeat_type: exact_repeat` 后，才能作为正式数据表述：
锁定 `original_seed` 和原始配置，`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`，
并声明 `restore_target_H`、`near_miss_tolerance_H` 和 `near_miss_not_restored`。接近但未达到目标
只能说明有效果、还有希望，不能说还原；同一候选无论是否还原成功都最多 5 次，5 次未还原不能继续加跑复现。换 seed 的 `seed_sweep` / `multi_seed_stability`
必须写 `not_confirmation_evidence: true`，只能作为搜索或稳定性诊断。

tune transition 默认只能进入：

```text
single_run_valid
tune_promising
rerun_required
rejected
stopped_no_gain
```
