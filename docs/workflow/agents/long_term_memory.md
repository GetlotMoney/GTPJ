# Long-Term Agent Memory

本文件定义 GTPJ 的长期 agent 机制。目标是让每个角色既有可持续的活上下文，又有可审计的文件化事实源。

## 核心定义

长期 agent 不是单纯的临时 sub-agent，也不是只存在于聊天窗口里的记忆。正式 GTPJ workflow 中，一个长期 agent 由两部分共同组成：

```text
persistent_thread_id / visible thread label
shared_roles/<role>/profile.md
shared_roles/<role>/memory.md
by_experiment/<task_type>/agents/README.md
agent_summary.md
review_round_*.md
docs/workflow/issues/YYYY-MM-DD-*.md
```

persistent thread 负责保留角色自己的连续上下文、右侧栏可见过程和长期运行中的细节经验。
`profile.md` / `memory.md` / issues / agent summary / review 文件负责可提交、可审计、可复核的长期事实。

线程上下文可能压缩、漂移或丢失局部细节，所以它不能单独作为正式证据。进入 `result.yaml`、
`quality_check.md`、promotion 证据或正式结论前，仍必须回到当前 repo、Research、Warehouse artifact 或日志验证。

正式 `real_multi_agent` 默认使用：

```yaml
agents:
  activation_mode: real_multi_agent
  agent_instance_mode: persistent_thread
```

运行时 `temporary_subagent` 可以作为一次性加速、只读复核或 fallback，但每次启动前必须加载对应长期角色文件。
实例结束后，新的经验写回文件化记忆或长期 thread 的可见总结，而不是只留在临时对话里。

创新代码改动中的临时 agents 还必须遵守：

```text
docs/workflow/innovation_code_review_protocol.md
```

也就是说，临时 agent 可以承担 Reader/Planner、Interface Checker、Quality Checker、Reviewer、
Log Analyst 或 Result Analyst 的一次性独立审查，但它必须显式接收长期角色文件和本轮审查输入，并把结论写入
`review_round_*.md`、`agent_summary.md` 或 `docs/workflow/issues/`。临时 agent 的隐藏上下文不能作为
正式证据，也不能替代长期角色 persistent thread 完成正式 best、promotion 或 owner 明确要求的长期多 agent 工作。

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
1. 对应角色 persistent thread id / thread label
2. shared_roles/<role>/profile.md
3. shared_roles/<role>/memory.md
4. by_experiment/<task_type>/agents/README.md
5. docs/workflow/issues/README.md 和最近相关问题文档
6. 当前 task start card
```

真实多 agent 下，Coordinator 必须在 sub-agent 任务说明里写明这些输入文件，不能假设 sub-agent
自动知道主 agent 的隐藏上下文。

Task Start Card 和 Agent Summary 必须记录：

```text
agent_instance_mode: persistent_thread | temporary_subagent | role_only
persistent_thread_id:
persistent_thread_reused: yes | no
temporary_subagent_reason:
```

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
- Task Start Card 和 Agent Summary 记录实际读取了哪些 profile / memory 文件，以及使用了哪个 persistent thread。
- 如果 GitHub 和本地 skill 不一致，GitHub 为准，并阻断正式实验。
