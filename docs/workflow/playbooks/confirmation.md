# 执行卡：复现 / 确认 Confirmation

用于复现或确认一个结果。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
experiment_protocol.md
quality_gate.md
产生 raw artifact 时读 ARTIFACT_REGISTRATION.md
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

## Repeat 规则

默认 confirmation 跑 3 次。

如果复现通过：

```text
official single = best repeat
reported stability = mean / min / max
```

不能隐藏较弱 repeat。稳定性属于正式证据的一部分。

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
