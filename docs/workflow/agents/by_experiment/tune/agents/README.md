# Tune Agents

## 默认模式更新

正式 tune run 默认使用 `real_multi_agent`。Reader/Planner、Runner、Log Analyst、Quality Checker、Result Analyst 必须按角色隔离上下文；Runner 仍然串行。

`role_only` 只允许用于训练前最多 3 个候选建议、纯配置查看，或明确不登记正式证据的 debug/smoke。

本文件用于 version-level tune。调参只改变正式 baseline `vX` 的参数，不改变模型结构。
训练串行，一次只跑一个 Runner。

如果调的是某个 module trial 内部的 attempt 参数，例如 heads、ratio、dropout、seed，
使用 `module_trial_protocol.md` 的 trial-internal `param_tune`，写入该 trial 的
`ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，不使用本 version-level tune agent 编排。

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
- 当前版本从 `main` 开 `exp/vX-tune-...`。
- 历史版本从 `vX` tag 开临时运行分支。
- version-level 长期轻量证据只写 `experiments/vX/tune/`；完整日志、checkpoint、generated figures 留在 Warehouse。
- 历史版本跑完证据回当前 `main`，然后删除临时运行分支。
- 如记录 `promotion_decision: promote` 和 `promote_to`，转交 promotion agents。
