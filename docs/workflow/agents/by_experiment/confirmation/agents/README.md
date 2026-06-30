# Confirmation Agents

## 默认模式更新

正式 confirmation / rerun 默认使用 `real_multi_agent` + `agent_instance_mode: persistent_thread`。Runner 仍然串行，但 Log Analyst、Quality Checker、Result Analyst 必须使用独立上下文；promotion 前或争议结果还必须启用 Reviewer。

`role_only` 只允许用于准备冻结配置、查看复现状态，或明确不登记正式证据的 debug/smoke。

`temporary_subagent` 只能作为一次性加速或只读复核；正式复现结论、best 复核和 promotion-facing 结论必须回到长期角色 thread 与文件化 evidence。

本文件用于 version-level confirmation。重新复现用于验证已有 baseline 或版本级结果是否可信。

如果确认对象是某个 module trial 的 `best_attempt_id`，使用 `module_trial_protocol.md` 的
trial-internal clean `confirmation`，写入该 trial 的 `ATTEMPTS.md` 和
`attempts/ATTEMPT-xxx/`，不写入 `experiments/vX/confirmation/`。

## 启用角色

```text
Coordinator
Runner
Log Analyst
Quality Checker
Result Analyst
```

## 默认禁用角色

```text
Implementer
Interface Checker
Reviewer, unless promotion-facing or disputed evidence
```

## 编排

```text
Coordinator -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

## 关键规则

- 固定 `base_code_tag`。
- 固定 config、seed、命令、数据 split 和 cache 口径。
- 不改模型结构。
- Runner 串行运行。
- Runner 只写 Warehouse raw artifacts。
- Log Analyst 记录 U/S/H/ZS、best epoch、log artifact id、URI、hash 和失败阶段。
- Quality Checker 确认证据完整，并确认 dataset split、label mapping、class order、metric calculation 与 baseline 可比。
- Coordinator 收口 `agent_summary.md`；不保存完整聊天流水，只保存角色、检查范围、发现、结论和证据引用。
- 复现失败只记录证据和下一步建议，不直接改 baseline。
