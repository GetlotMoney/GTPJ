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

- Quality Checker 检查 hard gate 证据、artifact hash、GitHub 边界和 Warehouse 引用。
- Interface Checker 只在来源为消融或创新等代码改动时必须启用。
- Result Analyst 确认指标、delta、U/S/ZS、seed、best epoch、对照 seed 和目标版本合理。
- Interface Checker 必须确认 class order、seen/unseen split、label mapping、logits shape 和 metric calculation 没有未声明变化。
- Coordinator 硬门通过后自动创建本地版本材料和本地 tag。
- Coordinator 默认只把版本账本回流到 `main`。
- `main` 当前代码是否切到新版本，必须由 owner 明确执行 `activate-version`。
- 不自动 push GitHub。
- promotion 分支从当前 `main` 开，不整体合并旧实验分支，也不默认整体合并回 `main`。
