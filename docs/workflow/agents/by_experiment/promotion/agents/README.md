# Promotion Agents

Promotion agents 在实验记录已经写出 `promotion_decision: promote` 和 `promote_to: vX` 后启动。

## 启用角色

```text
Coordinator
Quality Checker
Interface Checker
Result Analyst
```

## 编排

```text
Coordinator -> Quality Checker + Interface Checker + Result Analyst -> Coordinator
```

## 关键规则

- Quality Checker 检查 hard gate 证据。
- Interface Checker 只在来源为消融或创新等代码改动时必须启用。
- Result Analyst 确认指标、delta、U/S/ZS、seed、best epoch 和目标版本合理。
- Coordinator 硬门通过后自动创建本地版本材料和本地 tag。
- 不自动 push GitHub。
- promotion 分支从当前 `main` 开，不整体合并旧实验分支。
