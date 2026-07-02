# 执行卡：调参 Tune

用于参数、seed、epoch、batch、loss weight 或不改变方法语义的窄配置搜索。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
GZSL_HARD_RULES.md
AGENT_RUNTIME_HARD_GATE.md
experiment_protocol.md
产生 raw artifact 时读 ARTIFACT_REGISTRATION.md
```

如果调参发生在 module trial 内部，还要读：

```text
module_trial_protocol.md
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

正式 Runner 启动前必须写 `agent_runtime.yaml`，记录右侧临时 agents 的真实
`agent_instance_id`，并通过 `validate-agent-runtime`。否则本轮 tune 只能是
debug/smoke 或候选线索。

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

重要 tuned config 必须 3 次 confirmation 后，才能作为正式数据表述。

tune transition 默认只能进入：

```text
single_run_valid
tune_promising
rerun_required
rejected
stopped_no_gain
```
