# 执行卡：消融 Ablation

用于移除、替换、关闭或隔离某个组件。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
experiment_protocol.md
code_interface_contract.md
产生 raw artifact 时读 ARTIFACT_REGISTRATION.md
```

如果消融发生在 module trial 内部，还要读：

```text
module_trial_protocol.md
```

## 角色

正式默认角色：

```text
总控 (Coordinator)
阅读/规划 (Reader/Planner)
接口检查 (Interface Checker)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

只有需要改代码时才加入 `实现者 (Implementer)`。

## 阻断门

- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚。
- 消融暗中改变了目标组件之外的东西。
- 要和 unconfirmed baseline 比较，却没有标出这个边界。
