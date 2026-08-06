# Tune Agents

## 默认模式更新

正式 tune run 默认使用 `real_multi_agent` + workflow-scoped `named_owner_thread`。Reader/Planner、Runner、Log Analyst、Quality Checker、Result Analyst 必须按角色隔离上下文；Runner 仍然串行。

`role_only` 只允许用于训练前最多 3 个候选建议、纯配置查看，或明确不登记正式证据的 debug/smoke。

`named_owner_thread` 可以覆盖本轮 tune workflow；正式结果解释、best 候选判断和 promotion-facing 结论必须回到 `agent_summary.md`、result、quality 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。

本文件用于正式框架 tune。调参只改变 `FRAMEWORK-VX` 的参数，不改变模型结构。
训练串行，一次只跑一个 Runner。

如果参数来源于旧 module trial，例如 heads、ratio、dropout、seed，也使用本编排并写入所属正式框架的
`tune/` 账本；旧 Trial/Attempt 只通过 `legacy_ref` 追溯。

## 启用角色

```text
Coordinator
Reader / Planner
Runner
Log Analyst
Quality Checker
Result Analyst
```

## 禁用角色

```text
Implementer
Interface Checker
Reviewer
```

除非 Coordinator 明确发现调参请求已经变成代码结构改动，否则不启用这些角色。

## 编排

```text
Coordinator -> Reader/Planner -> 用户选择 -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

## 关键规则

- Reader / Planner 先给最多 3 个调参建议。
- 用户只能选择 1 个建议进入本轮运行。
- Runner 只跑用户选中的一个实验。
- Runner 只写 Warehouse raw artifacts，不把 raw log 写进 GitHub。
- Log Analyst 解析 Warehouse 日志，Coordinator 只写 `manifest.yaml`、`result.yaml` 和 `result.md`。
- Coordinator 必须写 `agent_summary.md`，记录参与 agents、禁用 agents、检查范围、发现和证据引用。
- 新调参从目标 `framework/vX` 开 `exp/vX/tune/TUNE-...`。
- framework tune 长期轻量证据只写 `experiments/vX/tune/`；完整日志、checkpoint、generated figures 留在 Warehouse。
- 实验证据写回目标框架账本，并同步当前 `main` 总索引；确认入账后可删除临时实验分支。
- 如记录 `promotion_decision: promote` 和 `promote_to`，转交 promotion agents。
