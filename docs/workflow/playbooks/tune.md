# 执行卡：调参 Tune

用于参数、seed、epoch、batch、loss weight 或不改变方法语义的窄配置搜索。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
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
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

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
