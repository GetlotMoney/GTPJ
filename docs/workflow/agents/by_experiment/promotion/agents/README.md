# Promotion Agents

Promotion agents 在实验记录已经写出 `promotion_decision: promote`、`promote_to: vX`、
`evidence_level: baseline_grade` 和 `confirmation_status: confirmed` 后启动。

Promotion 必须保留 `agent_summary.md`，记录 Quality Checker、Interface Checker、Result Analyst 和 Reviewer 的准入结论。长报告放 Warehouse，GitHub 只保存摘要和 artifact id。

Promotion 默认使用 `real_multi_agent` + `agent_instance_mode: persistent_thread`。临时 sub-agent 不能替代长期角色 thread 给出最终通过结论；如果 thread 缺失，必须阻断或记录 owner 接受的 debug-only fallback。

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
- Quality Checker 必须拒绝只有 `best_observed_H`、缺 `confirmed_H` 的 promotion。
- Interface Checker 只在来源为消融或创新等代码改动时必须启用。
- Result Analyst 确认指标、delta、U/S/ZS、seed、best epoch、对照 seed 和目标版本合理。
- Interface Checker 必须确认 class order、seen/unseen split、label mapping、logits shape 和 metric calculation 没有未声明变化。
- Coordinator 硬门通过后自动创建本地版本材料和本地 tag。
- Coordinator 默认只把版本账本回流到 `main`。
- `main` 当前代码是否切到新版本，必须由 owner 明确执行 `activate-version`。
- 不自动 push GitHub。
- promotion 分支从当前 `main` 开，不整体合并旧实验分支，也不默认整体合并回 `main`。
