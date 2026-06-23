# Ablation Agents

消融可以改代码，但代码是临时实验代码，不自动进入 `main`。

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
- Interface Checker 必须在训练前检查维度、logits、loss、labels、class order、mask 和 config switch。
- Runner 串行运行。
- 必须保留 `implementation.md`、`code.diff`、`interface_check.md`、`quality_check.md` 和结果证据。
- 跑完只把证据写入 `experiments/vX/ablation/`。
- 即使效果更好，也必须走 promotion agents，不能把临时代码直接并入 `main`。
