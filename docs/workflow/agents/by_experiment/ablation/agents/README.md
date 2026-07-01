# Ablation Agents

本文件用于 version-level ablation。消融可以改代码，但代码是临时实验代码，不自动进入 `main`。

正式 ablation run 默认使用 `real_multi_agent` + workflow-scoped `temporary_subagent`。Interface Checker、Log Analyst、Quality Checker 和 Result Analyst 必须保留独立上下文；正式结论必须写回 `agent_summary.md`、interface、quality、result 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。

如果消融对象只是某个 module trial 当前实现假设下的局部因素，使用 `module_trial_protocol.md`
的 trial-internal narrow `ablation`，写入该 trial 的 `ATTEMPTS.md` 和
`attempts/ATTEMPT-xxx/`，不写入 `experiments/vX/ablation/`。

## 启用角色

```text
Coordinator
Reader / Planner
Implementer
Interface Checker
Runner
Log Analyst
Quality Checker
Result Analyst
```

## 编排

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

## 关键规则

- 一次只消融一个主要因素。
- 必须记录 `disabled_module` 或 `disabled_factor`。
- 必须记录 `switch_key` 或旁路位置。
- Implementer 只做最小临时代码改动。
- Interface Checker 必须在训练前检查维度、logits、loss、labels、label mapping、seen/unseen split、class order、mask 和 config switch。
- Runner 串行运行。
- Runner 只写 Warehouse raw artifacts。
- 必须保留 `implementation.md`、`code.diff`、`interface_check.md`、`quality_check.md`、`agent_summary.md`、`manifest.yaml`、`result.yaml` 和 `result.md`。
- version-level 消融跑完只把轻量证据写入 `experiments/vX/ablation/`；raw logs、checkpoint、generated figures 留在 Warehouse。
- 即使效果更好，也必须走 promotion agents，不能把临时代码直接并入 `main`。
