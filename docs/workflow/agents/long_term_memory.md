# Long-Term Agent Memory

本文件定义 GTPJ 的长期 agent 机制。目标是减少重复犯错，而不是把聊天窗口当记忆。

## 核心定义

长期 agent 不是一个永久在线的进程。长期 agent 是一个持久身份包：

```text
shared_roles/<role>/profile.md
shared_roles/<role>/memory.md
by_experiment/<task_type>/agents/README.md
agent_summary.md
docs/workflow/issues/YYYY-MM-DD-*.md
```

运行时 sub-agent 可以是临时实例，但每次启动前必须加载对应长期身份包。实例结束后，
新的经验写回文件化记忆，而不是留在临时对话里。

创新代码改动中的临时 agents 还必须遵守：

```text
docs/workflow/innovation_code_review_protocol.md
```

也就是说，临时 agent 可以承担 Reader/Planner、Interface Checker、Quality Checker、Reviewer、
Log Analyst 或 Result Analyst 的独立审查，但它必须显式接收长期角色文件和本轮审查输入，并把结论写入
`review_round_*.md`、`agent_summary.md` 或 `docs/workflow/issues/`。临时 agent 的隐藏上下文不能作为
正式证据。

## 每个角色的长期文件

每个 `shared_roles/<role>/` 至少包含：

```text
profile.md  # 身份、职责、读写边界、失败条件
memory.md   # 长期经验、重复错误、固定检查项
```

`memory.md` 使用下面结构：

```text
# <Role> Memory

## Standing Lessons
长期有效经验。

## Recurrent Failure Modes
重复出错模式和预防规则。

## Required Checks
每次执行该角色都必须检查的事项。

## Update Rules
什么时候更新本文件。
```

## 启动加载规则

Coordinator 激活某个角色时，必须让该角色读取或显式接收：

```text
1. shared_roles/<role>/profile.md
2. shared_roles/<role>/memory.md
3. by_experiment/<task_type>/agents/README.md
4. docs/workflow/issues/README.md 和最近相关问题文档
5. 当前 task start card
```

真实多 agent 下，Coordinator 必须在 sub-agent 任务说明里写明这些输入文件，不能假设 sub-agent
自动知道主 agent 的隐藏上下文。

## 记忆写回规则

每次任务结束时，Coordinator 检查是否需要写回长期记忆：

| 触发 | 写入位置 |
|---|---|
| 本次具体问题、失败、修复 | `docs/workflow/issues/YYYY-MM-DD-*.md` |
| 某角色反复犯同类错误 | `shared_roles/<role>/memory.md` |
| 多角色共同边界问题 | `docs/workflow/agent_orchestration.md` 或 `agent_report_policy.md` |
| 重复后处理动作 | `workflow/gtpj_workflow.py` helper 或 sync check |

规则：

- 新问题出现 1 次，先写 issue。
- 同类问题出现 2 次，写入对应角色 memory。
- 同类手工后处理出现 3 次，升级成 helper 或自动校验。

## 证据边界

`memory.md` 是提醒和检查清单，不是实验事实源。进入正式结论前仍必须验证：

```text
当前 repo 文件
commit / tag
config / manifest / result / quality_check
Warehouse artifact
Research source review
```

未验证的 memory-derived fact 不能写入 `result.yaml`、`quality_check.md`、promotion 证据或正式结论。

## 自动对齐

长期 agent 体系需要被 `sync-check` 覆盖：

- GitHub `docs/workflow/agents/` 中每个角色都有 `profile.md` 和 `memory.md`。
- 本地 `gtpj-workflow` skill 镜像这些文件。
- Task Start Card 和 Agent Summary 记录实际读取了哪些 profile / memory 文件。
- 如果 GitHub 和本地 skill 不一致，GitHub 为准，并阻断正式实验。
